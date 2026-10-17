; Semantic page offsets; no text/portrait cache. Original entries stay two-page.
PokedexDescription_GetMetadata:
; a=transient species ID; carry=custom and hl=three offsets. Preserve bc/de.
	push de
	call GetPokemonIndexFromID
	ld de, -TREECKO
	add hl, de
	ld a, h
	and a
	jr nz, .original
	ld a, l
	cp NUM_POKEMON - TREECKO + 1
	jr nc, .original
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
	ld de, PokedexDescriptionPageOffsets
	add hl, de
	pop de
	scf
	ret
.original
	pop de
	and a
	ret

PokedexDescription_GetPageCount:
; a=transient species ID; return count in a. Preserve bc/de.
	call PokedexDescription_GetMetadata
	ld a, 2
	ret nc
	inc hl
	inc hl
	ld a, [hl]
	and a
	ld a, 4
	ret nz
	dec hl
	ld a, [hl]
	and a
	ld a, 3
	ret nz
	dec a
	ret

PokedexDescription_GetPageOffset:
; a=species ID, c=zero-based page; carry=custom, a=relative offset.
; Preserve bc/de. Page zero and absent/out-of-range pages return offset zero.
	call PokedexDescription_GetMetadata
	ret nc
	ld a, c
	and a
	jr z, .zero
	cp 4
	jr nc, .zero
	dec a
	add l
	ld l, a
	jr nc, .read
	inc h
.read
	ld a, [hl]
	scf
	ret
.zero
	xor a
	scf
	ret

PokedexDescription_SeekStaticPage:
; b=entry bank, c=page, de=page-one text. Return de=requested text, b unchanged.
; Only hidden/staged entry construction uses this synchronous legacy scan.
	ld a, [wTempSpecies]
	call PokedexDescription_GetPageOffset
	jr nc, .original
	ld l, a
	ld h, 0
	add hl, de
	ld d, h
	ld e, l
	ret
.original
	ld a, c
	and a
	ret z
.scan
	ld h, d
	ld l, e
	ld a, b
	call GetFarByte
	inc de
	cp "@"
	jr nz, .scan
	dec c
	jr nz, .scan
	ret

INCLUDE "data/pokemon/dex_description_page_offsets.asm"
