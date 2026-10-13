PokedexRuntime_RecordROMRecipe:
; Reuse the old source-pointer slots, no new RAM. Record the prepared page,
; not the subsequently requested page, so cancellation cannot change the key.
	ld a, [wPrevDexEntry]
	ld [wPokedexInfoTileSources], a
	ld a, [wPrevDexEntry + 1]
	ld [wPokedexInfoTileSources + 1], a
	ld a, [wPokedexInfoPage]
	ld [wPokedexInfoTileSources + 2], a
	ret

PokedexRuntime_CopyROMTiles:
	ld a, [wPokedexRuntimeReturnRepair]
	and a
	jr z, .ready
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
	ld a, c
	and a
	jr nz, .tile
	push bc
	call PokedexRuntime_PrepareROMSources
	pop bc
.tile
	push bc
	call PokedexRuntime_ROMTileAddress
	push hl
	ld a, [wPokedexInfoCopyTile]
	call PokedexRuntime_GFXAddress
	ld d, h
	ld e, l
	pop hl
	ld bc, TILE_SIZE
	ld a, BANK(PokedexROMRestoreGFX)
	call FarCopyBytes
	ld hl, wPokedexInfoCopyTile
	inc [hl]
	pop bc
	inc c
	dec b
	jr nz, .tile
	ret
.ready
	ld a, [wPokedexInfoTileCount]
	ld [wPokedexInfoCopyTile], a
	ld a, POKEDEX_INFO_UPLOAD
	ld [wPokedexInfoState], a
	ret

PokedexRuntime_PrepareROMSources:
; Resolve once per recovery. These three existing runtime fields are unused
; by semantic-ROM preparation, so this does not allocate another cache.
	ld a, [wPokedexInfoTileSources]
	ld l, a
	ld a, [wPokedexInfoTileSources + 1]
	ld h, a
	ld a, [wPokedexInfoTileSources + 2]
	and a
	jr nz, .evolution
	ld b, h
	ld c, l
	ld hl, BaseData
	ld a, BANK(BaseData)
	call LoadIndirectPointer
	jr .cache
.evolution
	push af
	dec hl
	add hl, hl
	ld de, PokedexROMRestoreSpecies
	add hl, de
	ld a, BANK(PokedexROMRestoreSpecies)
	call GetFarWord
	pop af
	dec a
	add a
	ld e, a
	ld d, 0
	add hl, de
	ld a, BANK(PokedexROMRestoreSpecies)
	call GetFarWord
	ld a, BANK(PokedexROMRestoreSpecies)
.cache
	ld [wPokedexRuntimeLevelBank], a
	ld a, l
	ld [wPokedexRuntimeLevelSource], a
	ld a, h
	ld [wPokedexRuntimeLevelSource + 1], a
	ret

PokedexRuntime_ROMTileAddress:
; C is the committed atlas slot. Return an immutable recovery glyph pointer.
	ld a, [wPokedexInfoTileSources + 2]
	and a
	jr nz, .evolution
	ld a, c
	cp POKEDEX_INFO_SHARED_TILES
	jr nc, .number
	add a
	ld e, a
	ld d, 0
	ld hl, PokedexROMRestoreShared
	add hl, de
	jr .pointer
.number
	sub POKEDEX_INFO_SHARED_TILES
	push af
	srl a
	srl a
	ld l, a
	ld h, 0
	ld de, .StatOrder
	add hl, de
	ld a, [hl]
	ld e, a
	ld d, 0
	call .cached_pointer
	add hl, de
	ld a, [wPokedexRuntimeLevelBank]
	call GetFarByte
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, PokedexROMRestoreNumbers
	add hl, de
	pop af
	and 3
	add a
	ld e, a
	ld d, 0
	add hl, de
	jr .pointer
.evolution
	call .cached_pointer
	ld a, c
	add a
	ld e, a
	ld d, 0
	add hl, de
.pointer
	ld a, BANK(PokedexROMRestoreSpecies)
	jp GetFarWord
.cached_pointer
	ld a, [wPokedexRuntimeLevelSource]
	ld l, a
	ld a, [wPokedexRuntimeLevelSource + 1]
	ld h, a
	ret
.StatOrder db 1, 2, 3, 5, 6, 4
