; PRIVATE A/B PROTOTYPE ONLY. Not included by any production build.
SECTION "Private selective portrait mask", ROMX[$7b00], BANK[$77]

PrototypeSelectiveMask:
	ld a, [wPokedexSelectedState]
	cp 2
	jr z, .mask
	ld a, B_Pokedex_BlackOutBG
	ld hl, Pokedex_BlackOutBG
	rst FarCall
	ret
.mask
	ldh a, [rSVBK]
	push af
	ld a, B_wBGPals1
	ldh [rSVBK], a
	ld hl, wBGPals1 + 8
	call .white_two_palettes
	ld hl, wBGPals1 + 48
	call .white_two_palettes
	pop af
	ldh [rSVBK], a
	ret
.white_two_palettes
	ld b, 8
.color
	ld a, $ff
	ld [hli], a
	ld a, $7f
	ld [hli], a
	dec b
	jr nz, .color
	ret
PrototypeSelectiveMaskEnd:
