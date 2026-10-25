SECTION "Budget Fused Font", ROMX[PROBE_PC], BANK[PROBE_BANK]
BudgetFont:
    ld hl, Font
    ld de, $8800
IF DEF(PREPARED_FONT)
    ld hl, .Prepared
IF DEF(USE_GDMA)
    ld a, h
    ldh [$ff51], a
    ld a, l
    ldh [$ff52], a
    ld a, $08
    ldh [$ff53], a
    xor a
    ldh [$ff54], a
    ld a, $7f
    ldh [$ff55], a
ELSE
    ld bc, 2048
    call CopyBytes
ENDC
ELSE
    ld b, 128 / UNROLL
.tile
REPT 8 * UNROLL
    xor a
    ld [de], a
    inc de
    ld a, [hli]
    cpl
    ld [de], a
    inc de
ENDR
    dec b
    jr nz, .tile
ENDC
    ret
IF DEF(PREPARED_FONT)
IF DEF(USE_GDMA)
    ds (-@) & 15, 0
ENDC
.Prepared
    INCBIN PREPARED_FONT_PATH
ENDC
BudgetFontEnd:
