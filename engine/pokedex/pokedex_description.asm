Pokedex_IsDescriptionLayout:
	ld a, [wJumptableIndex]
	cp DEXSTATE_SELECTED_MON_ENTER
	jr c, .other
	cp DEXSTATE_SELECTED_MON_RESERVED + 1
	jr nc, .other
	ld a, [wPokedexSelectedView]
	and a
	jr nz, .other
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_LEAVING
	jr z, .other
	scf
	ret
.other
	and a
	ret

Pokedex_LoadDescriptionGFX:
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld de, PokedexDescriptionGFX
	ld hl, vTiles2 tile POKEDEX_DESCRIPTION_GFX_TILE
	lb bc, BANK(PokedexDescriptionGFX), (PokedexDescriptionGFXEnd - PokedexDescriptionGFX) / TILE_SIZE
	call Get2bpp
	pop af
	ldh [rVBK], a
	ret

Pokedex_DrawDescriptionScreenBG:
	ld hl, PokedexDescriptionTilemap
	decoord 0, 0
	ld bc, SCREEN_AREA
	call CopyBytes
	hlcoord 9, 5
	ld de, .Height
	call .PlaceString
	hlcoord 9, 6
	ld de, .Weight
	call .PlaceString
	hlcoord 0, 17
	ld de, .MenuItems
	call .PlaceString
	farcall Pokedex_PlaceFrontpicTopLeftCorner
	ret
.PlaceString:
	ld a, [de]
	cp -1
	ret z
	inc de
	ld [hli], a
	jr .PlaceString
.Height:
	db "Ht  ?", $5e, "??", $5f, -1
.Weight:
	db "Wt   ???lb", -1
.MenuItems:
	db $3b, " Desc Stat Mov Area", -1

Pokedex_DisplayDescriptionEntry:
	farcall DisplayDexEntry
	; The shared registration printer owns the old divider and page badge.
	; Restore this owner's border after either description page is printed.
	ld hl, PokedexDescriptionTilemap + 8 * SCREEN_WIDTH
	decoord 0, 8
	ld bc, SCREEN_WIDTH
	call CopyBytes
	hlcoord 1, 9
	ld [hl], POKEDEX_DESCRIPTION_GFX_TILE + 6
	inc hl
	ld [hl], POKEDEX_DESCRIPTION_GFX_TILE + 7
	ld a, [wPokedexDescriptionPage]
	and a
	ret z
	hlcoord 2, 8
	ld [hl], POKEDEX_DESCRIPTION_GFX_TILE + 8
	hlcoord 2, 9
	ld [hl], POKEDEX_DESCRIPTION_GFX_TILE + 9
	ret

Pokedex_StageDescriptionRightEdge:
	ld hl, PokedexDescriptionRightEdge
	ld de, wPokedexOwnerTilemapBuffer + SCREEN_WIDTH
	ld c, SCREEN_HEIGHT
.tiles
	ld a, [hli]
	ld [de], a
	ld a, e
	add TILEMAP_WIDTH
	ld e, a
	jr nc, .next_tile
	inc d
.next_tile
	dec c
	jr nz, .tiles
	ld hl, wPokedexOwnerAttrmapBuffer + SCREEN_WIDTH
	ld c, SCREEN_HEIGHT
.attrs
	xor a
	ld [hl], a
	ld de, TILEMAP_WIDTH
	add hl, de
	dec c
	jr nz, .attrs
	ret

Pokedex_CopyDescriptionRightEdge:
	; SCX=5 exposes five pixels of BG column 20 beyond the backing map.
	ldh a, [rVBK]
	push af
	ld a, BANK(vBGMap2)
	ldh [rVBK], a
	ld de, vBGMap0 + SCREEN_WIDTH
	ld c, SCREEN_HEIGHT
.attrs
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .attrs
	xor a
	ld [de], a
	call .NextRow
	dec c
	jr nz, .attrs
	xor a
	ldh [rVBK], a
	ld hl, PokedexDescriptionRightEdge
	ld de, vBGMap0 + SCREEN_WIDTH
	ld c, SCREEN_HEIGHT
.tiles
	ld a, [hli]
	ld b, a
.wait
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait
	ld a, b
	ld [de], a
	call .NextRow
	dec c
	jr nz, .tiles
	pop af
	ldh [rVBK], a
	ret
.NextRow:
	ld a, e
	add TILEMAP_WIDTH
	ld e, a
	ret nc
	inc d
	ret

Pokedex_LoadDescriptionTypeGFX:
	ldh a, [hCGB]
	and a
	ret z
	ld a, [wPokedexSelectedSpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBaseType1]
	ld de, wPokedexWRAM0Scratch
	call .CopyType
	ld a, [wBaseType1]
	ld b, a
	ld a, [wBaseType2]
	cp b
	ld c, ICON_COMPACT_TYPE_TILES
	jr z, .upload
	ld de, wPokedexWRAM0Scratch + ICON_COMPACT_TYPE_TILES tiles
	call .CopyType
	ld c, 2 * ICON_COMPACT_TYPE_TILES
.upload
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles5)
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles5 tile POKEDEX_DESCRIPTION_TYPE_TILE
	call Pokedex_HDMATransferCacheGFX
	pop af
	ldh [rVBK], a
	ld a, POKEDEX_DESCRIPTION_TYPE_TILE
	hlcoord 9, 7
	call .PlaceType
	ld a, [wBaseType1]
	ld b, a
	ld a, [wBaseType2]
	cp b
	ret z
	ld a, POKEDEX_DESCRIPTION_TYPE_TILE + ICON_COMPACT_TYPE_TILES
	hlcoord 14, 7
.PlaceType:
	ld c, ICON_COMPACT_TYPE_TILES
.place
	ld [hli], a
	inc a
	dec c
	jr nz, .place
	ret
.CopyType:
	push de
	ld e, a
	ld d, 0
	ld hl, CompactTypeIconGFXPointers
	add hl, de
	add hl, de
	add hl, de
	ld a, BANK(CompactTypeIconGFXPointers)
	call GetFarByte
	push af
	inc hl
	ld a, BANK(CompactTypeIconGFXPointers)
	call GetFarWord
	pop af
	pop de
	push de
	ld bc, ICON_COMPACT_TYPE_TILES tiles
	call FarCopyBytes
	pop hl
	; Round only this owner's badge corners into palette color 1 (background).
	set 7, [hl]
	ld bc, 14
	add hl, bc
	set 7, [hl]
	ld c, 34
	add hl, bc
	set 0, [hl]
	ld c, 14
	add hl, bc
	set 0, [hl]
	ret

Pokedex_SetDescriptionTypeAttrsAndPals:
	ld hl, .FootprintPalette
	ld de, wBGPals1 palette POKEDEX_DESCRIPTION_FOOTPRINT_PAL
	ld bc, 1 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	ld a, [wBaseType1]
	ld de, wBGPals1 palette POKEDEX_DESCRIPTION_TYPE1_PAL
	call .LoadTypePalette
	hlcoord 9, 7, wAttrmap
	ld a, BG_BANK1 | POKEDEX_DESCRIPTION_TYPE1_PAL
	ld bc, ICON_COMPACT_TYPE_TILES
	call ByteFill
	ld a, [wBaseType1]
	ld b, a
	ld a, [wBaseType2]
	cp b
	jr z, .dirty
	ld de, wBGPals1 palette POKEDEX_DESCRIPTION_TYPE2_PAL
	call .LoadTypePalette
	hlcoord 14, 7, wAttrmap
	ld a, BG_BANK1 | POKEDEX_DESCRIPTION_TYPE2_PAL
	ld bc, ICON_COMPACT_TYPE_TILES
	call ByteFill
.dirty
	ld hl, wPokedexSelectedBGPaletteDirty
	ld a, [hl]
	or (1 << POKEDEX_DESCRIPTION_FOOTPRINT_PAL) | (1 << POKEDEX_DESCRIPTION_TYPE1_PAL) | (1 << POKEDEX_DESCRIPTION_TYPE2_PAL)
	ld [hl], a
	ret
.LoadTypePalette:
	push de
	ld e, a
	ld d, 0
	ld hl, TypeIconPalettePointers
	add hl, de
	add hl, de
	ld a, BANK(TypeIconPalettePointers)
	call GetFarWord
	pop de
	ldh a, [rSVBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rSVBK], a
	push de
	ld a, BANK(TypeIconPalettes)
	ld bc, 1 palettes
	call FarCopyBytes
	pop hl
	inc hl
	inc hl
	ld [hl], LOW((5 << 10) | (5 << 5) | 5)
	inc hl
	ld [hl], HIGH((5 << 10) | (5 << 5) | 5)
	pop af
	ldh [rSVBK], a
	ret
.FootprintPalette:
	RGB 31, 31, 31
	RGB 0, 0, 0
	RGB 0, 0, 0
	RGB 5, 5, 5

; Fixed shell data follows. Frontpic, text, footprint and type badges are
; supplied by their existing owners after this background is copied.

PokedexDescriptionGFX:
	; $71: divider left
	db %11111100, %00000001
	db %11111100, %00000001
	db %11111100, %00000000
	db %11111111, %00000000
	db %11111111, %00000000
	db %11111100, %00000000
	db %11111100, %00000001
	db %11111100, %00000001
	; $72: P. badge upper left
	db %00000000, %11111111
	db %00000000, %11111111
	db %00000000, %00000000
	db %11111111, %00000000
	db %11111111, %00000000
	db %00000000, %00000000
	db %00000000, %10111111
	db %00000000, %10100011
	; $73: page 1 upper right
	db %00000000, %11111111
	db %00000000, %11111111
	db %00000000, %00000000
	db %11111111, %00000000
	db %11111111, %00000000
	db %00000000, %00000000
	db %00000000, %11111101
	db %00000000, %11001101
	; $74: divider
	db %00000000, %11111111
	db %00000000, %11111111
	db %00000000, %00000000
	db %11111111, %00000000
	db %11111111, %00000000
	db %00000000, %00000000
	db %00000000, %11111111
	db %00000000, %11111111
	; $75: divider join
	db %00100000, %10001111
	db %00100000, %10001111
	db %00100000, %00000000
	db %11111111, %00000000
	db %11111111, %00000000
	db %00000000, %00000000
	db %00000000, %11111111
	db %00000000, %11111111
	; $76: divider right
	db %00001111, %11100000
	db %00001111, %11100000
	db %00001111, %00000000
	db %11111111, %00000000
	db %11111111, %00000000
	db %00001111, %00000000
	db %00001111, %11100000
	db %00001111, %11100000
	; $77: P. badge lower left
	db %00000000, %10101011
	db %00000000, %10100011
	db %00000000, %10101110
	db %00000000, %10111111
	db %00000000, %10000000
	db %00000000, %11111111
	db %00000000, %11111111
	db %00000000, %11111111
	; $78: page 1 lower right
	db %00000000, %11101101
	db %00000000, %11101101
	db %00000000, %11101101
	db %00000000, %11111101
	db %00000000, %00000001
	db %00000000, %11111111
	db %00000000, %11111111
	db %00000000, %11111111
	; $79: page 2 upper right
	db %00000000, %11111111
	db %00000000, %11111111
	db %00000000, %00000000
	db %11111111, %00000000
	db %11111111, %00000000
	db %00000000, %00000000
	db %00000000, %11111101
	db %00000000, %10000101
	; $7a: page 2 lower right
	db %00000000, %11100101
	db %00000000, %10011101
	db %00000000, %10000101
	db %00000000, %11111101
	db %00000000, %00000001
	db %00000000, %11111111
	db %00000000, %11111111
	db %00000000, %11111111
PokedexDescriptionGFXEnd:

PokedexDescriptionTilemap:
	db $33, $34, $34, $34, $34, $34, $34, $34, $59, $34, $34, $34, $34, $34, $34, $34, $34, $34, $34, $34
	db $36, $62, $62, $62, $62, $62, $62, $62, $5a, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $62, $62, $62, $62, $62, $62, $62, $5a, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $62, $62, $62, $62, $62, $62, $62, $5a, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $62, $62, $62, $62, $62, $62, $62, $5a, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $62, $62, $62, $62, $62, $62, $62, $5a, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $62, $62, $62, $62, $62, $62, $62, $5a, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $62, $62, $62, $62, $62, $62, $62, $5a, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $71, $72, $73, $74, $74, $74, $74, $74, $75, $74, $74, $74, $74, $74, $74, $74, $74, $74, $74, $74
	db $36, $77, $78, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $36, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
	db $38, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39, $39
	db $3b, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32, $32
.end
	assert .end - PokedexDescriptionTilemap == SCREEN_AREA

PokedexDescriptionRightEdge:
	db $66, $67, $67, $67, $67, $67, $67, $67, $76, $67, $67, $67, $67, $67, $67, $67, $68, $3c
.end
	assert .end - PokedexDescriptionRightEdge == SCREEN_HEIGHT
	assert POKEDEX_DESCRIPTION_GFX_TILE + (PokedexDescriptionGFXEnd - PokedexDescriptionGFX) / TILE_SIZE <= $80
	assert POKEDEX_DESCRIPTION_TYPE_TILE >= POKEDEX_ANIM_BUFFER_B_TILE + 7 * 7
	assert POKEDEX_DESCRIPTION_TYPE_TILE + 2 * ICON_COMPACT_TYPE_TILES <= $80
