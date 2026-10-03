; PRIVATE PREFLIGHT ONLY. Two records reuse the existing bank-3 Tower union.
; Each inactive record is prepared before its atlas is published. Cancellation
; never changes the visible selector or its matching immutable source pointers.
PokedexInfo_BeginRecord:
	xor a
	ld [wPokedexInfoRow], a
	ld a, POKEDEX_INFO_RECORD
	ld [wPokedexInfoState], a
	ret

PokedexInfo_RecordAddress:
	ld de, wPokedexInfoReturnRecordA
	ld a, [wPokedexInfoAtlasBuffer]
	and a
	ret z
	ld de, wPokedexInfoReturnRecordB
	ret

PokedexInfo_RecordPage:
; Six slices of at most 64 bytes; no bulk copy inside the VBlank publisher.
	call PokedexInfo_RecordAddress
	ld a, [wPokedexInfoRow]
	cp 4
	jr nc, .sources
	add a
	add a
	add a
	add a
	add a
	add a
	ld l, a
	ld h, 0
	push hl
	add hl, de
	ld d, h
	ld e, l
	pop hl
	ld bc, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
	add hl, bc
	ld bc, 64
	ld a, [wPokedexInfoRow]
	cp 3
	jr nz, .copy
	ld c, 32
	jr .copy
.sources
	ld hl, 7 * TILEMAP_WIDTH
	cp 5
	jr nz, .first_sources
	ld hl, 7 * TILEMAP_WIDTH + 64
.first_sources
	add hl, de
	ld d, h
	ld e, l
	ld hl, wPokedexInfoTileSources
	ld bc, 64
	ld a, [wPokedexInfoRow]
	cp 5
	jr nz, .copy
	ld hl, wPokedexInfoTileSources + 64
	ld c, 16
.copy
	call CopyBytes
	ld hl, wPokedexInfoRow
	inc [hl]
	ld a, [hl]
	cp 6
	ret nz
	; DE is now the count field at record + 304.
	ld a, [wPokedexInfoTileCount]
	ld [de], a
	ld a, POKEDEX_INFO_READY
	ld [wPokedexInfoState], a
	ret

PokedexInfo_PreserveReturnPanel:
; Caller has canceled all producers. Hardware OAM and palettes stay untouched.
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
	ld a, [wPokedexInfoVisible]
	and a
	jp z, .done
	ld a, [wPokedexInfoActiveAtlasBuffer]
	and a
	jp z, .done
	ld a, TRUE
	ldh [hOAMUpdate], a
	xor a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
.relocate
	ld hl, wPokedexInfoReturnRecordB
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
	ld bc, 7 * TILEMAP_WIDTH
	call CopyBytes
	ld de, wPokedexInfoTileSources
	ld bc, POKEDEX_INFO_TILES * 2
	call CopyBytes
	ld a, [hl]
	ld [wPokedexInfoTileCount], a
	xor a
	ld [wPokedexInfoAtlasBuffer], a
	ld [wPokedexInfoCopyTile], a
	ld [wPokedexInfoUploadTile], a
.copy
	ld a, [wPokedexInfoCopyTile]
	ld hl, wPokedexInfoTileCount
	cp [hl]
	jr nc, .upload
	call PokedexInfo_CopyTiles
	jr .copy
.upload
	ld a, [wPokedexInfoUploadTile]
	ld hl, wPokedexInfoTileCount
	cp [hl]
	jr nc, .remap
	call PokedexInfo_UploadTiles
	jr .upload
.remap
	; These captured maps have no bank-0 IDs below 40: the only low IDs
	; are atlas-B glyphs. Shell/title/page cells are permanent IDs >= 40.
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
	ld b, 7 * TILEMAP_WIDTH
.cell
	ld a, [de]
	cp POKEDEX_INFO_TILES
	jr nc, .next
	push bc
	add a
	ld c, a
	ld b, 0
	ld hl, PokedexInfoAtlasCells
	add hl, bc
	ld a, [hl]
	ld [de], a
	pop bc
.next
	inc de
	dec b
	jr nz, .cell
	ld a, POKEDEX_OWNER_TRANSITION_INFO_RETURN
	ld [wPokedexOwnerTransition], a
	ld a, VBLANK_POKEDEX
	ldh [hVBlank], a
.wait
	call DelayFrame
	ld a, [wPokedexOwnerTransition]
	and a
	jr nz, .wait
.done
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ret
