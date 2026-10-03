; PRIVATE PREFLIGHT ONLY. Included by info_return_preflight.py, never main.asm.
; Caller has canceled text/Info/portrait/cry work and has IME enabled.
PokedexInfo_PreserveReturnPanel:
	ldh a, [hCGB]
	and a
	ret z
	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld a, [wPokedexInfoListingCacheDirty]
	and a
	jp z, .done
	; Freeze actual hardware OAM/palettes, not an unfinished job's targets.
	ld a, TRUE
	ldh [hOAMUpdate], a
	xor a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	ld a, 1
	ldh [rVBK], a
	ld hl, vBGMap0 + 9 * TILEMAP_WIDTH
	ld de, wPokedexOwnerAttrmapBuffer + 9 * TILEMAP_WIDTH
	ld bc, 7 * TILEMAP_WIDTH
	call .ReadVRAM
	xor a
	ldh [rVBK], a
	ld hl, vBGMap0 + 9 * TILEMAP_WIDTH
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
	ld bc, 7 * TILEMAP_WIDTH
	call .ReadVRAM
	ld hl, wPokedexOwnerAttrmapBuffer + 9 * TILEMAP_WIDTH
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
	ld b, 7 * TILEMAP_WIDTH
.find_borrowed
	ld a, [hli]
	bit B_BG_BANK1, a
	jr z, .next_cell
	ld a, [de]
	cp POKEDEX_INFO_TILES
	jr c, .relocate
.next_cell
	inc de
	dec b
	jr nz, .find_borrowed
	jp .done
.relocate
	ld a, 1
	ldh [rVBK], a
	ld hl, vTiles5
	ld de, wPokedexInfoGFX
	ld bc, POKEDEX_INFO_TILES * TILE_SIZE
	call .ReadVRAM
	xor a
	ld [wPokedexInfoAtlasBuffer], a
	ld [wPokedexInfoUploadTile], a
	ld a, POKEDEX_INFO_TILES
	ld [wPokedexInfoTileCount], a
.upload
	ld a, [wPokedexInfoUploadTile]
	cp POKEDEX_INFO_TILES
	jr nc, .remap
	call PokedexInfo_UploadTiles
	jr .upload
.remap
	ld hl, wPokedexOwnerAttrmapBuffer + 9 * TILEMAP_WIDTH
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
	ld b, 7 * TILEMAP_WIDTH
.remap_cell
	ld a, [hli]
	bit B_BG_BANK1, a
	jr z, .next_remap
	ld a, [de]
	cp POKEDEX_INFO_TILES
	jr nc, .next_remap
	push hl
	push bc
	add a
	ld c, a
	ld b, 0
	ld hl, PokedexInfoAtlasCells
	add hl, bc
	ld a, [hl]
	ld [de], a
	pop bc
	pop hl
.next_remap
	inc de
	dec b
	jr nz, .remap_cell
	; All atlas-A cells use the same bank bit. Only tile IDs need publication.
	ld a, POKEDEX_OWNER_TRANSITION_INFO_RETURN
	ld [wPokedexOwnerTransition], a
	ld a, VBLANK_POKEDEX
	ldh [hVBlank], a
.wait_publication
	call DelayFrame
	ld a, [wPokedexOwnerTransition]
	and a
	jr nz, .wait_publication
.done
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ret
.ReadVRAM
	; Per-byte exclusion prevents an IRQ between the access check and read.
	di
.wait_vram
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_vram
	ld a, [hli]
	ld [de], a
	inc de
	ei
	dec bc
	ld a, b
	or c
	jr nz, .ReadVRAM
	ret
