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
