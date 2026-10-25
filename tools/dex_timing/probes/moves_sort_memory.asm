DEF MOVES_SORT_MEMORY_TAG EQU $a0

; All registers and bank ownership survive. Unknown/legacy values mean Type.
PokedexMovesMode_RestoreSort::
    push af
    push bc
    ldh a, [rSVBK]
    push af
    ld a, BANK(wLastMovesDexSort)
    ldh [rSVBK], a
    ld a, [wLastMovesDexSort]
    cp MOVES_SORT_MEMORY_TAG + 1
    ld b, 0
    jr nz, .decoded
    inc b
.decoded
    ld a, BANK(wPokedexInfoGFX)
    ldh [rSVBK], a
    ld a, b
    ld [wMovesModeSort], a
    pop af
    ldh [rSVBK], a
    pop bc
    pop af
    ret

; A is the confirmed Type/Alphabet choice. Never write SRAM from the menu.
PokedexMovesMode_RememberSort::
    push af
    cp 2
    jr nc, .done
    push bc
    ld b, a
    ldh a, [rSVBK]
    push af
    ld a, BANK(wLastMovesDexSort)
    ldh [rSVBK], a
    ld a, b
    or MOVES_SORT_MEMORY_TAG
    ld [wLastMovesDexSort], a
    pop af
    ldh [rSVBK], a
    pop bc
.done
    pop af
    ret
