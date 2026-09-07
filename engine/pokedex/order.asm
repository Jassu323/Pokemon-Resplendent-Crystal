ASSERT POKEDEX_GRID_SIDE_FRAME1_GFX + 8 tiles == POKEDEX_ORDER_SEEN_FLAGS
ASSERT POKEDEX_ORDER_SEEN_FLAGS + POKEDEX_ORDER_SEEN_BYTES <= wPokedexWRAM0ScratchEnd

Pokedex_OrderMonsByMode:
	ld hl, wEndPokedexSeen - 1
	ld c, wEndPokedexSeen - wPokedexSeen
.last_seen_loop
	ld a, [hld]
	and a
	jr nz, .found_last_seen
	dec c
	jr nz, .last_seen_loop
.found_last_seen
	ld [wDexLastSeenValue], a
	dec c
	and a ; flags are preserved until the jump; the following operations are loads and a push
	ld a, c
	ld [wDexLastSeenIndex], a

	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	ld hl, wPokedexOrder
	ld a, -1
	jr z, .nothing_seen
	ld bc, (NUM_POKEMON + 1) * 2
	call ByteFill
	ld a, [wCurDexMode]
	ld hl, .Jumptable
	call .LoadPointer
	call _hl_
.restore_bank_and_exit
	pop af
	ldh [rSVBK], a
	ret

.nothing_seen
	ld [hli], a
	ld [hl], a
	xor a
	ld hl, wDexListingEnd
	ld [hli], a
	ld [hl], a
	ld hl, POKEDEX_ORDER_SEEN_FLAGS
	ld bc, POKEDEX_ORDER_SEEN_BYTES
	call ByteFill
	jr .restore_bank_and_exit

.Jumptable:
	dw .NewMode
	dw .OldMode
	dw .ABCMode

.LoadPointer:
	ld e, a
	ld d, 0
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret

.OldMode:
	ld a, [wDexLastSeenValue] ; known to be non-zero
	ld c, 9 ; bits are numbered 1-8 because the first dex entry is #001, not #000
.highest_bit_index_loop
	dec c
	add a, a
	jr nc, .highest_bit_index_loop
	ld a, [wDexLastSeenIndex]
	ld l, a
	ld h, 0
	ld b, h
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, bc
	ld d, h
	ld e, l
	ld hl, wPokedexOrder
	ld c, b ; b = 0
.old_mode_loop
	inc bc
	ld a, c
	ld [hli], a
	ld a, b
	ld [hli], a
	cp d
	jr c, .old_mode_loop
	ld a, c
	cp e
	jr c, .old_mode_loop
	ld hl, wDexListingEnd
	ld a, e
	ld [hli], a
	ld [hl], d
	; Old order position n corresponds directly to species index n + 1.
	ld a, BANK(wPokedexSeen)
	ldh [rSVBK], a
	ld hl, wPokedexSeen
	ld de, POKEDEX_ORDER_SEEN_FLAGS
	ld bc, POKEDEX_ORDER_SEEN_BYTES
	jp CopyBytes

.NewMode:
	ld hl, NewPokedexOrder
	ld de, wPokedexOrder
	ld bc, NUM_POKEMON * 2
	call CopyBytes
	; New order permutes species, so build a position-keyed eligibility mask
	; while finding the position immediately after its final seen entry.
	ld a, BANK(wPokedexSeen)
	ldh [rSVBK], a
	ld hl, POKEDEX_ORDER_SEEN_FLAGS
	ld bc, POKEDEX_ORDER_SEEN_BYTES
	xor a
	call ByteFill
	ld hl, wDexListingEnd
	ld [hli], a
	ld [hl], a
	ld hl, NewPokedexOrder
	ld bc, 0
.new_mode_seen_loop
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	push hl
	push bc
	call CheckSeenMonIndex
	pop bc
	pop hl
	jr z, .new_mode_next
	push hl
	push bc
	ld d, b
	ld e, c
	ld hl, POKEDEX_ORDER_SEEN_FLAGS
	ld b, SET_FLAG
	call FlagAction
	pop bc
	pop hl
	inc bc
	ld a, c
	ld [wDexListingEnd], a
	ld a, b
	ld [wDexListingEnd + 1], a
	jr .new_mode_check_end

.new_mode_next
	inc bc
.new_mode_check_end
	ld a, b
	cp HIGH(NUM_POKEMON)
	jr nz, .new_mode_seen_loop
	ld a, c
	cp LOW(NUM_POKEMON)
	jr nz, .new_mode_seen_loop
	ret

.ABCMode:
	call Pokedex_ABCMode
	; ABC mode compacts the order to seen Pokemon only.
	ld hl, POKEDEX_ORDER_SEEN_FLAGS
	ld bc, POKEDEX_ORDER_SEEN_BYTES
	ld a, $ff
	jp ByteFill

Pokedex_ABCMode:
	; called in the WRAM bank of wPokedexOrder; the function doesn't preserve it
	ld hl, wDexTempCounter
	ld a, LOW(-NUM_POKEMON)
	ld [hli], a
	ld [hl], HIGH(-NUM_POKEMON)
	ld bc, AlphabeticalPokedexOrder
	ld de, wPokedexOrder
	ld a, BANK(wPokedexSeen)
	ldh [rSVBK], a
.loop
	push de
	ld a, [bc]
	ld e, a
	inc bc
	ld a, [bc]
	ld d, a
	push bc
	call CheckSeenMonIndex
	pop bc
	pop de
	jr z, .skip
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	dec bc
	ld a, [bc]
	ld [de], a
	inc de
	inc bc
	ld a, [bc]
	ld [de], a
	inc de
	ld a, BANK(wPokedexSeen)
	ldh [rSVBK], a
.skip
	inc bc
	ld hl, wDexTempCounter
	inc [hl]
	jr nz, .loop
	inc hl
	inc [hl]
	jr nz, .loop
	ld hl, $10000 - wPokedexOrder ; ld hl, -wPokedexOrder -- see https://github.com/rednex/rgbds/issues/279
	add hl, de
	srl h
	rr l
	ld a, l
	ld [wDexListingEnd], a
	ld a, h
	ld [wDexListingEnd + 1], a
	ret

INCLUDE "data/pokemon/dex_order_alpha.asm"

INCLUDE "data/pokemon/dex_order_new.asm"
