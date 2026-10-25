SECTION "Budget LCD On Font", ROMX[PROBE_PC], BANK[PROBE_BANK]
BudgetFontLCD:
    ldh a, [$ff70]
    push af
    ld a, B_wDecompressScratch
    ldh [$ff70], a
    ld hl, Font
    ld de, wDecompressScratch
    ld bc, 1024
.convert
    ld a, [hli]
    ld [de], a
    inc de
    ld [de], a
    inc de
    dec bc
    ld a, b
    or c
    jr nz, .convert
    ld de, wDecompressScratch
    ld hl, $8800
    ld b, PROBE_BANK
    ld c, 64
    call Get2bppViaHDMA
    ld de, wDecompressScratch + 1024
    ld hl, $8c00
    ld b, PROBE_BANK
    ld c, 64
    call Get2bppViaHDMA
    pop af
    ldh [$ff70], a
    ret
BudgetFontLCDEnd:
