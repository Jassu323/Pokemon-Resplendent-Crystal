; Selected-only composition executes beside the native font, avoiding per-glyph
; ROM bank switches and intermediate copies. No shared font consumer calls it.
ASSERT BANK(PokedexRuntime_FontPair) == BANK(Font)
PokedexRuntime_FontPair::
	ld a, [wPokedexRuntimePreviousChar]
	call .pointer
	push hl
	ld a, [wPokedexRuntimeGlyph]
	call .pointer
	ld d, h
	ld e, l
	pop hl
	ld bc, wPokedexRuntimeTile
	ld a, 8
	ld [wPokedexRuntimeRows], a
.row
	ld a, [wPokedexRuntimePhase]
	cp 1
	jr z, .one
	ld a, [hli]
	add a
	add a
	add a
	push af
	ld a, [de]
	inc de
	swap a
	rra
	and 7
	jr .combine
.one
	ld a, [hli]
	rrca
	and $80
	push af
	ld a, [de]
	inc de
	srl a
.combine
	ld [wPokedexRuntimeBits], a
	pop af
	push hl
	ld hl, wPokedexRuntimeBits
	or [hl]
	pop hl
	cpl
	push af
	xor a
	ld [bc], a
	inc bc
	pop af
	ld [bc], a
	inc bc
	ld a, [wPokedexRuntimeRows]
	dec a
	ld [wPokedexRuntimeRows], a
	jr nz, .row
	ret
.pointer
	cp ' '
	jr nz, .glyph
	ld a, $ca ; a validated blank cell in the native ROM font
.glyph
	sub $80
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	push de
	ld de, Font
	add hl, de
	pop de
	ret
