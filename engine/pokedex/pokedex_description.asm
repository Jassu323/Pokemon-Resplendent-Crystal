Pokedex_IsDescriptionLayout:
	ld a, [wJumptableIndex]
	cp DEXSTATE_SELECTED_MON_ENTER
	jr c, .other
	cp DEXSTATE_SELECTED_MON_RESERVED + 1
	jr nc, .other
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_INFO + 1
	jr nc, .other
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
	ld de, PokedexInfoPageGFX
	ld hl, vTiles2 tile $7b
	lb bc, BANK(PokedexInfoPageGFX), 4
	call Get2bpp
	ld a, 1
	ldh [rVBK], a
	ld de, PokedexInfoHPEndpointGFX
	ld hl, vTiles3 tile POKEDEX_INFO_HP_OBJ_TILE
	lb bc, BANK(PokedexInfoHPEndpointGFX), 2
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
	db $3b, " Desc Info Mov Area", -1

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
	farcall PokedexInfo_LoadTypeSprites
	ret


Pokedex_SetDescriptionTypeAttrsAndPals:
	ld hl, .FootprintPalette
	ld de, wBGPals1 palette POKEDEX_DESCRIPTION_FOOTPRINT_PAL
	ld bc, 1 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	ld hl, wPokedexSelectedBGPaletteDirty
	set POKEDEX_DESCRIPTION_FOOTPRINT_PAL, [hl]
	ret
.FootprintPalette:
	RGB 31, 31, 31
	RGB 0, 0, 0
	RGB 0, 0, 0
	RGB 5, 5, 5

PokedexInfoPageGFX:
	INCBIN "gfx/pokedex/pokedex_page_numbers.2bpp", 6 * TILE_SIZE, 4 * TILE_SIZE

; Fixed shell data follows. Frontpic, text, footprint and type badges are
; supplied by their existing owners after this background is copied.

PokedexDescriptionGFX:
	; The page sheet is column-major: P., 1..9, each upper tile then lower.
	; Pack only P./1/2 into the existing Description shell allocation.
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
	INCBIN "gfx/pokedex/pokedex_page_numbers.2bpp", 0 * TILE_SIZE, TILE_SIZE
	; $73: page 1 upper right
	INCBIN "gfx/pokedex/pokedex_page_numbers.2bpp", 2 * TILE_SIZE, TILE_SIZE
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
	INCBIN "gfx/pokedex/pokedex_page_numbers.2bpp", 1 * TILE_SIZE, TILE_SIZE
	; $78: page 1 lower right
	INCBIN "gfx/pokedex/pokedex_page_numbers.2bpp", 3 * TILE_SIZE, TILE_SIZE
	; $79: page 2 upper right
	INCBIN "gfx/pokedex/pokedex_page_numbers.2bpp", 4 * TILE_SIZE, TILE_SIZE
	; $7a: page 2 lower right
	INCBIN "gfx/pokedex/pokedex_page_numbers.2bpp", 5 * TILE_SIZE, TILE_SIZE
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
	assert POKEDEX_TYPE_OBJ_TILE >= 5 * ICON_4X2_TILES
	assert POKEDEX_TYPE_OBJ_TILE + 4 * ICON_COMPACT_TYPE_TILES <= POKEDEX_INFO_MINI_OBJ_TILE
	assert POKEDEX_INFO_MINI_OBJ_TILE + 4 * ICON_4X2_TILES <= POKEDEX_INFO_HP_OBJ_TILE
	assert POKEDEX_INFO_HP_OBJ_TILE + 2 <= $80
