LoadSGBPokedexGFX:
	ld hl, SGBPokedexGFX_LZ
	ld de, vTiles2 tile $31
	call Decompress
	ret

LoadSGBPokedexGFX2:
	ld hl, SGBPokedexGFX_LZ
	ld de, vTiles2 tile $31
	lb bc, BANK(SGBPokedexGFX_LZ), 58
	call DecompressRequest2bpp
	ret

SGBPokedexGFX_LZ:
INCBIN "gfx/pokedex/pokedex_sgb.2bpp.lz"

LoadQuestionMarkPic:
	ld hl, .QuestionMarkLZ
	ld de, sScratch
	call Decompress
	ret

.QuestionMarkLZ:
INCBIN "gfx/pokedex/question_mark.2bpp.lz"

Pokedex_CommitStagedSelection:
; Keep the old name and frontpic intact through their visible scanlines, then
; replace both later in the same frame. Palette and cursor OAM are queued by
; the caller for the following VBlank, revealing one complete new selection.
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .lcd_off

	ldh a, [rLY]
	cp 16
	jr c, .wait_name_row

.wait_next_frame
	ldh a, [rLY]
	cp 16
	jr nc, .wait_next_frame

.wait_name_row
	ldh a, [rLY]
	cp 16
	jr c, .wait_name_row

	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	hlcoord 0, 1
	ld de, vBGMap1 + TILEMAP_WIDTH
	ld c, 11
.copy_name
.wait_vram
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_vram
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .copy_name
	pop af
	ldh [rVBK], a

	ldh a, [rLY]
	cp 64
	jr c, .wait_frontpic_row

.wait_next_frontpic_frame
	ldh a, [rLY]
	cp 64
	jr nc, .wait_next_frontpic_frame

.wait_frontpic_row
	ldh a, [rLY]
	cp 64
	jr c, .wait_frontpic_row

	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles2
	ld c, 7 * 7
	call Pokedex_HDMATransferFrontpic
	ld a, [wCurPartySpecies]
	cp -1
	ret z
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch + 7 * 7 tiles
	ld de, vTiles4 tile $31
	ld c, 4
	call Pokedex_HDMATransferSelectionGFX
	pop af
	ldh [rVBK], a
	ld a, [wCurPartySpecies]
	ld [wPokedexResidentFootprintSpecies], a
	ret

.lcd_off
	hlcoord 0, 1
	ld de, vBGMap1 + TILEMAP_WIDTH
	ld bc, 11
	call CopyBytes
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles2
	ld bc, 7 * 7 tiles
	call CopyBytes
	ld a, [wCurPartySpecies]
	cp -1
	ret z
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch + 7 * 7 tiles
	ld de, vTiles4 tile $31
	ld bc, 4 tiles
	call CopyBytes
	pop af
	ldh [rVBK], a
	ld a, [wCurPartySpecies]
	ld [wPokedexResidentFootprintSpecies], a
	ret

Pokedex_CommitAnimationFrontpicMap::
; de = packed 7x7 tilemap immediately followed by packed attributes.
	ld h, d
	ld l, e
	push hl
	decoord 1, 1
	call Pokedex_CopyPackedFrontpicMapToBacking
	pop hl
	ld bc, 7 * 7
	add hl, bc
	decoord 1, 1, wAttrmap
	call Pokedex_CopyPackedFrontpicMapToBacking
	; fallthrough

Pokedex_CommitCurrentFrontpicMap::
; Reveal a complete map only after the frontpic's visible scanlines have
; passed. The graphics upload has already completed (or deliberately
; underrun) before this map is installed.
	xor a
	ldh [hBGMapMode], a
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .copy
	ldh a, [rLY]
	cp 64
	jr nc, .copy
.wait_frontpic
	ldh a, [rLY]
	cp 64
	jr c, .wait_frontpic
.copy
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	hlcoord 1, 1
	call Pokedex_CopyBackingFrontpicMapToVRAM
	ld a, BANK(vBGMap2)
	ldh [rVBK], a
	hlcoord 1, 1, wAttrmap
	call Pokedex_CopyBackingFrontpicMapToVRAM
	pop af
	ldh [rVBK], a
	ret

Pokedex_CopyPackedFrontpicMapToBacking:
	ld b, 7
.backing_row
	ld c, 7
.backing_col
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .backing_col
	ld a, e
	add SCREEN_WIDTH - 7
	ld e, a
	jr nc, .no_backing_carry
	inc d
.no_backing_carry
	dec b
	jr nz, .backing_row
	ret

Pokedex_CopyBackingFrontpicMapToVRAM:
	push hl
	ldh a, [hBGMapAddress]
	ld e, a
	ldh a, [hBGMapAddress + 1]
	ld d, a
	ld a, e
	add TILEMAP_WIDTH + 1
	ld e, a
	jr nc, .got_vram_dest
	inc d
.got_vram_dest
	pop hl
	ld b, 7
.vram_row
	ld c, 7
.vram_col
.wait_vram
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_vram
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .vram_col
	ld a, l
	add SCREEN_WIDTH - 7
	ld l, a
	jr nc, .no_source_carry
	inc h
.no_source_carry
	ld a, e
	add TILEMAP_WIDTH - 7
	ld e, a
	jr nc, .no_dest_carry
	inc d
.no_dest_carry
	dec b
	jr nz, .vram_row
	ret

Pokedex_UpdateGridOAM:
	call ClearSprites
	ld de, wShadowOAMSprite00
	ld a, 1
	lb bc, 40, POKEDEX_CENTER_ICON_TILE + 0 * 4
	ld l, OAM_BANK1 | 2
	call .PlaceCenterIcon
	ld de, wShadowOAMSprite04
	ld a, 4
	lb bc, 72, POKEDEX_CENTER_ICON_TILE + 1 * 4
	ld l, OAM_BANK1 | 3
	call .PlaceCenterIcon
	ld de, wShadowOAMSprite08
	ld a, 7
	lb bc, 104, POKEDEX_CENTER_ICON_TILE + 2 * 4
	ld l, OAM_BANK1 | 4
	call .PlaceCenterIcon

	ld de, wShadowOAMSprite12
	ld a, 0
	lb bc, 44, 64
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite13
	ld a, 1
	lb bc, 44, 96
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite14
	ld a, 2
	lb bc, 44, 128
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite15
	ld a, 3
	lb bc, 76, 64
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite16
	ld a, 4
	lb bc, 76, 96
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite17
	ld a, 5
	lb bc, 76, 128
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite18
	ld a, 6
	lb bc, 108, 64
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite19
	ld a, 7
	lb bc, 108, 96
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite20
	ld a, 8
	lb bc, 108, 128
	call .PlaceCaughtBall

	ld de, wShadowOAMSprite21
	call .PlaceCursor
	ld de, wShadowOAMSprite25
	ld a, 68
	ld h, 54
	ld c, POKEDEX_SCROLL_THUMB_TILE
	ld l, 5
	jp .WriteOAM

.PlaceCenterIcon:
; a = grid position, b = screen y, c = first tile, l = attributes
	push hl
	push bc
	ld l, a
	ld h, 0
	ld bc, wPokedexGridFlags
	add hl, bc
	bit POKEDEX_GRID_SEEN_F, [hl]
	pop bc
	pop hl
	ret z
	ld a, b
	ld h, 104
	call .WriteOAM
	inc c
	ld a, b
	ld h, 112
	call .WriteOAM
	inc c
	ld a, b
	add 8
	ld h, 104
	call .WriteOAM
	inc c
	ld a, b
	add 8
	ld h, 112
	jp .WriteOAM

.PlaceCaughtBall:
; a = grid position, b = screen y, c = screen x
	push bc
	ld l, a
	ld h, 0
	ld bc, wPokedexGridFlags
	add hl, bc
	bit POKEDEX_GRID_CAUGHT_F, [hl]
	pop bc
	ret z
	ld h, c
	ld a, b
	ld c, POKEDEX_CAUGHT_BALL_TILE
	ld l, 1
	jp .WriteOAM

.PlaceCursor:
	ld a, [wDexListingCursor]
	add a
	ld c, a
	ld b, 0
	ld hl, .CursorPositions
	add hl, bc
	ld a, [hli]
	ld [wDexTempCounter], a
	ld a, [hl]
	ld [wDexTempCounter + 1], a

	ld h, a
	ld a, [wDexTempCounter]
	ld c, POKEDEX_LIST_CURSOR_TILE
	ld l, 0
	call .WriteOAM
	ld a, [wDexTempCounter + 1]
	add 20
	ld h, a
	ld a, [wDexTempCounter]
	ld l, OAM_XFLIP
	call .WriteOAM
	ld a, [wDexTempCounter + 1]
	ld h, a
	ld a, [wDexTempCounter]
	add 20
	ld l, OAM_YFLIP
	call .WriteOAM
	ld a, [wDexTempCounter + 1]
	add 20
	ld h, a
	ld a, [wDexTempCounter]
	add 20
	ld l, OAM_XFLIP | OAM_YFLIP
	jp .WriteOAM

.WriteOAM:
; a = screen y, h = screen x, c = tile, l = attributes
	add 16
	ld [de], a
	inc de
	ld a, h
	add 8
	ld [de], a
	inc de
	ld a, c
	ld [de], a
	inc de
	ld a, l
	ld [de], a
	inc de
	ret

.CursorPositions:
	db 34, 66
	db 34, 98
	db 34, 130
	db 66, 66
	db 66, 98
	db 66, 130
	db 98, 66
	db 98, 98
	db 98, 130

Pokedex_UpdateGridCursorOAM:
; Static page OAM occupies slots 0-20 and 25. Selection changes only rewrite
; the four cursor corners in slots 21-24.
	ld de, wShadowOAMSprite21
	jp Pokedex_UpdateGridOAM.PlaceCursor

DrawPokedexListWindow:
	hlcoord 0, 0
	lb bc, SCREEN_HEIGHT, 12
	ld a, $32
	call FillBoxWithByte
	hlcoord 0, 1
	lb bc, 2, 11
	call ClearBox
	ld a, $34
	hlcoord 0, 0
	ld bc, 11
	call ByteFill
	ld a, $6b
	ld [hl], a
	ld a, $6c
	hlcoord 11, 1
	ld b, 1
	call Pokedex_FillColumn2
	ld a, $6d
	hlcoord 0, 2
	ld bc, 11
	call ByteFill
	ld [hl], $6e
	ld a, $34
	hlcoord 0, 3
	ld bc, 11
	call ByteFill
	ld a, $6b
	ld [hl], a
	ld a, $6c
	hlcoord 11, 4
	ld b, 12
	call Pokedex_FillColumn2
	ld a, $39
	hlcoord 0, 16
	ld bc, 11
	call ByteFill
	ld a, $6b
	ld [hl], a
	ld a, $31
	hlcoord 0, 17
	ld bc, 12
	call ByteFill
	hlcoord 5, 3
	ld [hl], $3f
	inc hl
	ld [hl], $40
	hlcoord 5, 16
	ld [hl], $3f
	inc hl
	ld [hl], $40

	ld a, 0
	hlcoord 1, 5
	ld c, POKEDEX_SIDE_ICON_TILE + 0 * 4
	call .PlaceGridEntry
	ld a, 1
	hlcoord 5, 5
	ld c, -1
	call .PlaceGridEntry
	ld a, 2
	hlcoord 9, 5
	ld c, POKEDEX_SIDE_ICON_TILE + 1 * 4
	call .PlaceGridEntry
	ld a, 3
	hlcoord 1, 9
	ld c, POKEDEX_SIDE_ICON_TILE + 2 * 4
	call .PlaceGridEntry
	ld a, 4
	hlcoord 5, 9
	ld c, -1
	call .PlaceGridEntry
	ld a, 5
	hlcoord 9, 9
	ld c, POKEDEX_SIDE_ICON_TILE + 3 * 4
	call .PlaceGridEntry
	ld a, 6
	hlcoord 1, 13
	ld c, POKEDEX_SIDE_ICON_TILE + 4 * 4
	call .PlaceGridEntry
	ld a, 7
	hlcoord 5, 13
	ld c, -1
	call .PlaceGridEntry
	ld a, 8
	hlcoord 9, 13
	ld c, POKEDEX_SIDE_ICON_TILE + 5 * 4
	call .PlaceGridEntry

	call .DrawAttrmap
	ret

.PlaceGridEntry:
; a = grid position, c = icon tile or -1 for an OAM column
	ld e, a
	ld d, 0
	push hl
	ld hl, wPokedexGridSpecies
	add hl, de
	ld a, [hl]
	and a
	jr z, .empty
	ld hl, wPokedexGridFlags
	add hl, de
	bit POKEDEX_GRID_SEEN_F, [hl]
	jr z, .unseen
	ld a, c
	cp -1
	jr z, .empty
	jr .place

.unseen
	ld a, POKEDEX_UNSEEN_TILE
.place
	pop hl
	ld [hli], a
	inc a
	ld [hl], a
	ld de, SCREEN_WIDTH - 1
	add hl, de
	inc a
	ld [hli], a
	inc a
	ld [hl], a
	ret

.empty
	pop hl
	ret

.DrawAttrmap:
	xor a
	hlcoord 0, 0, wAttrmap
	ld bc, SCREEN_AREA
	call ByteFill
	ld a, BG_YFLIP
	hlcoord 5, 16, wAttrmap
	ld [hli], a
	ld [hl], a
	hlcoord 11, 16, wAttrmap
	ld [hl], a

	ld a, 0
	hlcoord 1, 5, wAttrmap
	ld c, BG_BANK1 | 2
	call .SetGridIconAttr
	ld a, 2
	hlcoord 9, 5, wAttrmap
	ld c, BG_BANK1 | 3
	call .SetGridIconAttr
	ld a, 3
	hlcoord 1, 9, wAttrmap
	ld c, BG_BANK1 | 4
	call .SetGridIconAttr
	ld a, 5
	hlcoord 9, 9, wAttrmap
	ld c, BG_BANK1 | 5
	call .SetGridIconAttr
	ld a, 6
	hlcoord 1, 13, wAttrmap
	ld c, BG_BANK1 | 6
	call .SetGridIconAttr
	ld a, 8
	hlcoord 9, 13, wAttrmap
	ld c, BG_BANK1 | 7
	call .SetGridIconAttr
	ret

.SetGridIconAttr:
	ld e, a
	ld d, 0
	push hl
	ld hl, wPokedexGridFlags
	add hl, de
	bit POKEDEX_GRID_SEEN_F, [hl]
	jr z, .no_attr
	pop hl
	ld a, c
	ld [hli], a
	ld [hl], a
	ld de, SCREEN_WIDTH - 1
	add hl, de
	ld [hli], a
	ld [hl], a
	ret

.no_attr
	pop hl
	ret

DrawPokedexSearchResultsWindow:
	ld a, $34
	hlcoord 0, 0
	ld bc, 11
	call ByteFill
	ld a, $39
	hlcoord 0, 10
	ld bc, 11
	call ByteFill
	hlcoord 5, 0
	ld [hl], $3f
	hlcoord 5, 10
	ld [hl], $40
	hlcoord 11, 0
	ld [hl], $66
	ld a, $67
	hlcoord 11, 1
	ld b, SCREEN_HEIGHT / 2
	call Pokedex_FillColumn2
	ld [hl], $68
	ld a, $34
	hlcoord 0, 11
	ld bc, 11
	call ByteFill
	ld a, $39
	hlcoord 0, 17
	ld bc, 11
	call ByteFill
	hlcoord 11, 11
	ld [hl], $66
	ld a, $67
	hlcoord 11, 12
	ld b, 5
	call Pokedex_FillColumn2
	ld [hl], $68
	hlcoord 0, 12
	lb bc, 5, 11
	call ClearBox
	ld de, .esults_D
	hlcoord 0, 12
	call PlaceString
	ret

.esults_D
; (SEARCH R)
	db   "Esults"
	next ""
; (### FOUN)
	next "D!@"

DrawDexEntryScreenRightEdge:
	ldh a, [hBGMapAddress]
	ld l, a
	ldh a, [hBGMapAddress + 1]
	ld h, a
	push hl
	inc hl
	ld a, l
	ldh [hBGMapAddress], a
	ld a, h
	ldh [hBGMapAddress + 1], a
	hlcoord 19, 0
	ld [hl], $66
	hlcoord 19, 1
	ld a, $67
	ld b, 15
	call Pokedex_FillColumn2
	ld [hl], $68
	hlcoord 19, 17
	ld [hl], $3c
	xor a
	ld b, SCREEN_HEIGHT
	hlcoord 19, 0, wAttrmap
	call Pokedex_FillColumn2
	call WaitBGMap2
	pop hl
	ld a, l
	ldh [hBGMapAddress], a
	ld a, h
	ldh [hBGMapAddress + 1], a
	ret

Pokedex_FillColumn2:
; A local duplicate of Pokedex_FillColumn.
	push de
	ld de, SCREEN_WIDTH
.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	pop de
	ret
