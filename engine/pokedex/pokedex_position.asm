DEF POKEDEX_POSITION_TAG EQU $c0
ASSERT BANK(wPokemonDexBookmarkTag) == BANK(wMovesDexBookmarkTag)
ASSERT wPokemonDexBookmarkTag == wMovesDexBookmarkRow + 1
ASSERT wPokemonDexBookmarkCell == wMovesDexBookmarkTag + 7
ASSERT wPokemonDexBookmarkCell + 1 <= wPokecenter2FSceneID

; Only ordinary Listing B-exit owns this bookmark. Other owners retain their
; existing live Listing state; Search and Selected-result orders never record it.
Pokedex_RememberListingPosition:
	push af
	push bc
	push de
	push hl
	ldh a, [rSVBK]
	push af
	call Pokedex_ListingPositionTag
	jp c, .done
	ld a, [wPokedexListingPresentation]
	and a
	ld a, [wDexListingCursor]
	jr z, .grid_cell
	cp POKEDEX_LEGACY_HEIGHT
	jp nc, .done
	jr .cell_valid
.grid_cell
	cp POKEDEX_GRID_SIZE
	jp nc, .done
.cell_valid
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [wDexListingCursor]
	ld e, a
	ld d, 0
	add hl, de
	jp c, .done
	ld a, [wDexListingEnd]
	ld e, a
	ld a, [wDexListingEnd + 1]
	ld d, a
	ld a, h
	cp d
	jr c, .valid_index
	jr nz, .done
	ld a, l
	cp e
	jr nc, .done
.valid_index
	add hl, hl
	ld de, wPokedexOrder
	add hl, de
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	ld a, [hli]
	ld c, a
	ld a, [hl]
	ld b, a
	or c
	jr z, .done
	ld a, b
	cp HIGH(NUM_POKEMON)
	jr c, .valid_species
	jr nz, .done
	ld a, c
	cp LOW(NUM_POKEMON) + 1
	jr nc, .done
.valid_species
	ld a, BANK(wPokemonDexBookmarkTag)
	ldh [rSVBK], a
	ld hl, wPokemonDexBookmarkSpecies
	ld a, c
	ld [hli], a
	ld a, b
	ld [hli], a
	ld a, [wDexListingCursor]
	ld [hl], a
	call Pokedex_ListingPositionTag
	ld [wPokemonDexBookmarkTag], a
.done
	pop af
	ldh [rSVBK], a
	pop hl
	pop de
	pop bc
	pop af
	ret

; Run after order/layout setup and before cache priming or portrait preparation.
; Restore by permanent identity so newly seen Alphabet entries cannot retarget it.
Pokedex_RestoreListingPosition:
	push af
	push bc
	push de
	push hl
	ldh a, [rSVBK]
	push af
	xor a
	ld [wDexListingCursor], a
	ld [wDexListingScrollOffset], a
	ld [wDexListingScrollOffset + 1], a
	call Pokedex_ListingPositionTag
	jp c, .done
	ld c, a
	ld a, BANK(wPokemonDexBookmarkTag)
	ldh [rSVBK], a
	ld a, [wPokemonDexBookmarkTag]
	cp c
	jp nz, .done
	ld a, [wPokemonDexBookmarkCell]
	ld b, a
	ld a, [wPokedexListingPresentation]
	and a
	ld a, b
	jr z, .modern_cell
	cp POKEDEX_LEGACY_HEIGHT
	jp nc, .done
	jr .cell_valid
.modern_cell
	cp POKEDEX_GRID_SIZE
	jp nc, .done
.cell_valid
	push af
	ld a, [wPokemonDexBookmarkSpecies]
	ld e, a
	ld a, [wPokemonDexBookmarkSpecies + 1]
	ld d, a
	ld a, [wDexListingEnd]
	ld c, a
	ld a, [wDexListingEnd + 1]
	or c
	jr z, .not_found
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	ld hl, wPokedexOrder
	ld bc, 0
.scan
	ld a, [hli]
	cp e
	jr nz, .next
	ld a, [hl]
	cp d
	jr z, .found
.next
	inc hl
	inc bc
	ld a, [wDexListingEnd]
	cp c
	jr nz, .scan
	ld a, [wDexListingEnd + 1]
	cp b
	jr nz, .scan
.not_found
	pop af
	jp .done
.found
	pop af
	push bc
	ld e, a
	ld h, b
	ld l, c
	ld a, [wPokedexListingPresentation]
	and a
	jr nz, .position
	call Pokedex_AlignPositionRow
	ld a, e
	cp 2 * POKEDEX_GRID_WIDTH
	jr nc, .third_row
	cp POKEDEX_GRID_WIDTH
	ld e, 0
	jr c, .position
	ld e, POKEDEX_GRID_WIDTH
	jr .position
.third_row
	ld e, 2 * POKEDEX_GRID_WIDTH
.position
	ld a, l
	sub e
	ld l, a
	ld a, h
	sbc 0
	ld h, a
	jr nc, .maximum
	ld hl, 0
.maximum
	push hl
	ld a, [wDexListingEnd]
	ld l, a
	ld a, [wDexListingEnd + 1]
	ld h, a
	ld a, [wPokedexListingPresentation]
	and a
	ld de, POKEDEX_LEGACY_HEIGHT
	jr nz, .subtract_height
	inc hl
	inc hl
	call Pokedex_AlignPositionRow
	ld de, POKEDEX_GRID_SIZE
.subtract_height
	ld a, l
	sub e
	ld e, a
	ld a, h
	sbc d
	ld d, a
	jr nc, .clamp
	ld de, 0
.clamp
	pop hl
	ld a, h
	cp d
	jr c, .store
	jr nz, .last
	ld a, l
	cp e
	jr c, .store
.last
	ld h, d
	ld l, e
.store
	ld a, l
	ld [wDexListingScrollOffset], a
	ld a, h
	ld [wDexListingScrollOffset + 1], a
	pop bc
	ld a, c
	sub l
	ld [wDexListingCursor], a
.done
	pop af
	ldh [rSVBK], a
	pop hl
	pop de
	pop bc
	pop af
	ret

; Carry rejects unknown layout/order values; no transient identities are touched.
Pokedex_ListingPositionTag:
	ld a, [wCurDexMode]
	cp DEXMODE_ABC + 1
	jr nc, .invalid
	ld c, a
	ld a, [wPokedexListingPresentation]
	cp DEXLIST_LEGACY + 1
	jr nc, .invalid
	add a
	add a
	or c
	or POKEDEX_POSITION_TAG
	and a
	ret
.invalid
	scf
	ret

; Align HL down to a three-entry row. BC is scratch; DE is preserved.
Pokedex_AlignPositionRow:
	ld a, l
	add h
	jr nc, .reduce
	inc a
.reduce
	cp POKEDEX_GRID_WIDTH
	jr c, .remainder
	sub POKEDEX_GRID_WIDTH
	jr .reduce
.remainder
	ld c, a
	ld a, l
	sub c
	ld l, a
	ret nc
	dec h
	ret
