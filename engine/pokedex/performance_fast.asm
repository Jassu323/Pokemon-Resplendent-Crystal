; Dex performance helpers. No premium-memory allocation.
PokedexPerf_FastTownGFX:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a
	ld hl, TownMapGFX
	ld de, wPokedexOwnerTilemapBuffer
	ld a, BANK(TownMapGFX)
	call FarDecompress
	ld hl, wPokedexOwnerTilemapBuffer
	ld de, vTiles2
	ld c, 48
	call Pokedex_HDMATransferCacheGFX
	pop af
	ldh [rSVBK], a
	ret

PokedexPerf_FastTownMap:
; DE is the destination map. Area owns all graphics and has stopped the cry.
	push de
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a
	ld hl, wTilemap
	ld de, wPokedexOwnerTilemapBuffer
	call .pad
	ld hl, wAttrmap
	ld de, wPokedexOwnerAttrmapBuffer
	call .pad
	pop af
	pop de
	push af
	push de
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld hl, wPokedexOwnerTilemapBuffer
	ld c, 36
	call Pokedex_HDMATransferCacheGFX
	pop af
	push af
	ld a, 1
	ldh [rVBK], a
	pop af
	pop de
	push de
	push af
	ld hl, wPokedexOwnerAttrmapBuffer
	ld c, 36
	call Pokedex_HDMATransferCacheGFX
	pop af
	ldh [rVBK], a
	pop de
	pop af
	ldh [rSVBK], a
	ret
.pad
	ld b, SCREEN_HEIGHT
.row
REPT SCREEN_WIDTH
	ld a, [hli]
	ld [de], a
	inc de
ENDR
	ld a, e
	add TILEMAP_WIDTH - SCREEN_WIDTH
	ld e, a
	jr nc, .next
	inc d
.next
	dec b
	jr nz, .row
	ret

PokedexPerf_FastTownPals:
	ld hl, wTilemap
	ld de, wAttrmap
	ld bc, SCREEN_AREA
.cell
	push hl
	ld a, [hl]
	ld l, a
	ld h, 0
	push de
	ld de, PokedexPerf_TownPalTable
	add hl, de
	pop de
	ld a, [hl]
	pop hl
	inc hl
	ld [de], a
	inc de
	dec bc
	ld a, b
	or c
	jr nz, .cell
	ret

PokedexPerf_FastCopyTiles:
; This function lives with the glyph pool, so bank switching occurs once.
	ld a, [wPokedexInfoCopyTile]
	ld c, a
	ld a, [wPokedexInfoTileCount]
	sub c
	jr z, .ready
	cp 9
	jr c, .count
	ld a, 8
.count
	ld b, a
	ld h, 0
	ld l, c
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wPokedexInfoGFX
	add hl, de
	ld d, h
	ld e, l
	ld h, 0
	ld l, c
	add hl, hl
	ld a, LOW(wPokedexInfoTileSources)
	add l
	ld l, a
	ld a, HIGH(wPokedexInfoTileSources)
	adc h
	ld h, a
.tile
	ld a, [hli]
	ld c, [hl]
	inc hl
	push hl
	ld h, c
	ld l, a
REPT TILE_SIZE
	ld a, [hli]
	ld [de], a
	inc de
ENDR
	pop hl
	ld a, [wPokedexInfoCopyTile]
	inc a
	ld [wPokedexInfoCopyTile], a
	dec b
	jr nz, .tile
	ret
.ready
	ld a, POKEDEX_INFO_UPLOAD
	ld [wPokedexInfoState], a
	ret

PokedexPerf_TownPalTable:
INCBIN "build/dex-area-assets/town-pals.bin"
