; PRIVATE A/B PROTOTYPE ONLY. Not included by any production build.
SECTION "Private selective background mask", ROMX[$7b00], BANK[$77]

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
	; The portrait is white; footprint and type badges blend into the panel.
	ld hl, wBGPals1 + 8
	ld de, $7fff
	ld b, 4
	call .fill_palette_colors
	ld de, (5 << 10) | (5 << 5) | 5
	ld b, 4
	call .fill_palette_colors
	ld hl, wBGPals1 + 48
	ld b, 8
	call .fill_palette_colors
	pop af
	ldh [rSVBK], a
	ret
.fill_palette_colors
	ld a, e
	ld [hli], a
	ld a, d
	ld [hli], a
	dec b
	jr nz, .fill_palette_colors
	ret
PrototypeSelectiveMaskEnd:
