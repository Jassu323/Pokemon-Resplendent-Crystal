; Precomputed ancestor pages. No runtime glyph composition or shared ISR work.
PokedexAncestors_Header:
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
	add hl, hl
	ld de, PokedexInfoSpecies
	add hl, de
	ret

PokedexAncestors_PageCount:
	call PokedexAncestors_Header
	ld a, [hli]
	inc a
	srl a
	ld b, a
	inc hl
	inc hl
	ld a, [hl]
	inc a
	srl a
	add b
	inc a
	ld [wPokedexInfoPageCount], a
	ret

PokedexAncestors_GroupPage:
; hl is the selected group's count/pointer header; c is its local page.
	call PokedexAncestors_Header
	ld a, [hl]
	inc a
	srl a
	ld b, a
	ld a, [wPokedexInfoPage]
	and a
	jr z, .stats
	dec a
	cp b
	jr c, .group
	sub b
	inc hl
	inc hl
	inc hl
	jr .group
.stats
	xor a
.group
	ld c, a
	ret

PokedexAncestors_SelectPage:
; Groups never share a partly filled page. Each list entry is a word pointer.
	call PokedexAncestors_GroupPage
	inc hl
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, c
	add a
	add a
	ld e, a
	ld d, 0
	add hl, de
	ret

PokedexAncestors_DrawTitle:
	ld a, [wPokedexInfoPage]
	and a
	ld hl, PokedexInfoStatsTitle
	ld b, 0
	jr z, .draw
	push af
	call PokedexAncestors_Header
	ld a, [hl]
	inc a
	srl a
	ld b, a
	pop af
	dec a
	cp b
	ld hl, PokedexInfoEvolutionsTitle
	ld b, 0
	jr c, .draw
	ld hl, PokedexInfoEvolvesFromTitle
	ld b, OAM_BANK1
.draw
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH + 4
.letter
	ld a, [hli]
	cp '@'
	ret z
	ld [de], a
	push hl
	ld hl, wPokedexOwnerAttrmapBuffer - wPokedexOwnerTilemapBuffer
	add hl, de
	ld [hl], b
	pop hl
	inc de
	jr .letter

PokedexAncestors_PrepareTitle:
	ld a, [wPokedexInfoCaught]
	and a
	ret z
	call PokedexAncestors_Header
	inc hl
	inc hl
	inc hl
	ld a, [hl]
	and a
	ret z
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoMiniGFX)
	ldh [rSVBK], a
; Mini staging is dead here; committed minis and retained Info pixels stay in
; VRAM/their own buffers. Do not overwrite the primed portrait upload payload.
	ld hl, PokedexInfoAncestorTitleGFX
	ld de, wPokedexInfoMiniGFX
	ld bc, 13 tiles
	ld a, BANK(PokedexInfoAncestorTitleGFX)
	call FarCopyBytes
	call PokedexAncestors_UploadTitle
	pop af
	ldh [rSVBK], a
	ret

PokedexAncestors_RestoreUnownFont:
; Selected borrows the first thirteen bank-1 Unown glyph cells.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoMiniGFX)
	ldh [rSVBK], a
	ld hl, UnownFont
	ld de, wPokedexInfoMiniGFX
	ld bc, 13 tiles
	ld a, BANK(UnownFont)
	call FarCopyBytes
	ld hl, wPokedexInfoMiniGFX
	ld bc, 13 tiles
.invert
	ld a, [hl]
	xor $ff
	ld [hli], a
	dec bc
	ld a, b
	or c
	jr nz, .invert
	call PokedexAncestors_UploadTitle
	pop af
	ldh [rSVBK], a
	ret

PokedexAncestors_UploadTitle:
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexInfoMiniGFX
	ld de, vTiles4 tile $35
	ld bc, 13 tiles
	call PokedexAncestors_CopyTitleGFX
	pop af
	ldh [rVBK], a
	ret

PokedexAncestors_CopyTitleGFX:
; Static ROM pixels only. Guard pairs against mode 3 without a full-frame wait.
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jp z, CopyBytes
.pair
	di
.wait
	ldh a, [rSTAT]
	and 2
	jr nz, .wait
	ld a, [hli]
	ld [de], a
	inc de
	ld a, [hli]
	ld [de], a
	inc de
	ei
	dec bc
	dec bc
	ld a, b
	or c
	jr nz, .pair
	ret
