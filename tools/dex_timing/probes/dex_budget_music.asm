SECTION "Budget Cold Music Clock", ROMX[PROBE_PC], BANK[PROBE_BANK]
BudgetMusicBegin:
    ldh a, [$ff70]
    push af
    ld a, MUSIC_BANK
    ldh [$ff70], a
    xor a
    ld [MUSIC_RAM + 1], a
    ld [MUSIC_RAM + 2], a
    ld [MUSIC_RAM + 3], a
    ld [MUSIC_RAM + 4], a
    ldh a, [$ff07]
    and 7
    cp 4
    jr nz, .done
    ldh a, [$ff06]
    and a
    jr nz, .done
    ldh a, [$ff4d]
    bit 7, a
    jr z, .done
    ld a, 1
    ld [MUSIC_RAM + 4], a
    ldh a, [$ff05]
.sampled
    ld [MUSIC_RAM], a
.done
    pop af
    ldh [$ff70], a
    ret

BudgetMusicCheckpoint:
    push af
    push bc
    push de
    push hl
    ldh a, [$ff70]
    push af
    ld a, MUSIC_BANK
    ldh [$ff70], a
    ld a, [MUSIC_RAM + 4]
    and a
    jr z, .restore
    ldh a, [$ff05]
.sampled
    ld c, a
    ld hl, MUSIC_RAM
    sub [hl]
    ld [hl], c
    ld l, a
    ld h, 0
REPT 5
    add hl, hl
ENDR
    ld a, [MUSIC_RAM + 1]
    ld e, a
    ld a, [MUSIC_RAM + 2]
    ld d, a
    add hl, de
    ld c, 0
.frame
    ld a, h
    cp HIGH(4389)
    jr c, .record
    jr nz, .consume
    ld a, l
    cp LOW(4389)
    jr c, .record
.consume
    ld de, -4389
    add hl, de
    inc c
    jr .frame
.record
    ld a, l
    ld [MUSIC_RAM + 1], a
    ld a, h
    ld [MUSIC_RAM + 2], a
    ld a, [MUSIC_RAM + 3]
    add c
    ld [MUSIC_RAM + 3], a
    ld a, c
    and a
    jr z, .restore
    call SkipMusic
.restore
    pop af
    ldh [$ff70], a
    pop hl
    pop de
    pop bc
    pop af
    ret
BudgetMusicEnd:
