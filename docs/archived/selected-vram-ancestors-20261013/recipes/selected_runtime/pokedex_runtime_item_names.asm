; Bounded Selected-only item-name scanning beside the authoritative strings.
ASSERT BANK(PokedexRuntime_ItemTextChunk) == BANK(ItemNames)
PokedexRuntime_ItemTextChunk::
	ld a, [wPokedexRuntimeItemSource]
	ld l, a
	ld a, [wPokedexRuntimeItemSource + 1]
	ld h, a
	ld a, [wPokedexRuntimeTextAppend]
	ld e, a
	ld a, [wPokedexRuntimeTextAppend + 1]
	ld d, a
	ld b, 64
.byte
	ld a, [hli]
	ld c, a
	ld a, [wPokedexRuntimeItemRemaining]
	and a
	jr z, .copy
	ld a, c
	cp '@'
	jr nz, .next
	ld a, [wPokedexRuntimeItemRemaining]
	dec a
	ld [wPokedexRuntimeItemRemaining], a
	jr .next
.copy
	ld a, c
	ld [de], a
	inc de
	cp '@'
	jr nz, .next
	ld a, 4
	ld [wPokedexRuntimeTextState], a
	ret
.next
	dec b
	jr nz, .byte
	ld a, l
	ld [wPokedexRuntimeItemSource], a
	ld a, h
	ld [wPokedexRuntimeItemSource + 1], a
	ld a, e
	ld [wPokedexRuntimeTextAppend], a
	ld a, d
	ld [wPokedexRuntimeTextAppend + 1], a
	ret
