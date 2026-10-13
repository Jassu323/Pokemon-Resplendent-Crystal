; Semantic-only ancestor pages. No new WRAM, ISR work, or generated pixels.
PokedexRuntime_LoadAncestorTitle:
; Borrow the first thirteen Unown-font cells only while Selected is active.
; Regenerate before portrait/cry starts. Unown entry restores exactly these
; cells with GDMA; neither sidebar frames nor either Info atlas is touched.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexRuntimeTile)
	ldh [rSVBK], a
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld hl, PokedexRuntime_AncestorsText
	ld de, PokedexInfoEvolvesFromTitle
	call PokedexRuntime_LoadTitleWord
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ret

PokedexAncestors_RestoreUnownFont:
; Existing unbanked menu scratch is dead before Unown's own preparation.
	ld hl, UnownFont
	ld de, wPokedexWRAM0Scratch
	ld bc, 13 tiles
	ld a, BANK(UnownFont)
	call FarCopyBytes
	ld hl, wPokedexWRAM0Scratch
	ld bc, 13 tiles
.invert
	ld a, [hl]
	xor $ff
	ld [hli], a
	dec bc
	ld a, b
	or c
	jr nz, .invert
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles4 tile $35
	ld c, 13
	; This ROM0 wrapper preserves hl; farcall would replace the source pointer.
	call Pokedex_HDMATransferCacheGFX
	pop af
	ldh [rVBK], a
	ret

PokedexAncestors_CopyTitleTile:
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jp z, CopyBytes
	ld b, TILE_SIZE / 2
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
	dec b
	jr nz, .pair
	ret

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
	ld de, PokedexInfoSemanticSpecies
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

PokedexAncestors_SelectPage:
; Return this page's first record and at most two entries. Forward and
; ancestor groups start on separate pages, even if the first group is odd.
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
	add a
	ld b, a
	ld a, [hli]
	sub b
	jr nc, .remaining
	xor a
.remaining
	cp 3
	jr c, .count
	ld a, 2
.count
	ld [wPokedexRuntimeEvoCount], a
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, c
	add a
	add a
	add c
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
	ld b, 8
.draw
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH + 4
.letter
	ld a, [hli]
	cp "@"
	ret z
	ld [de], a
	push hl
	ld hl, wPokedexOwnerAttrmapBuffer - wPokedexOwnerTilemapBuffer
	add hl, de
	ld [hl], b
	pop hl
	inc de
	jr .letter
