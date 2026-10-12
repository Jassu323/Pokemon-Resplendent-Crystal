; Exclusive Type Matchups owner. Badge art and frame art are existing assets.
DEF TYPES_STATE EQUS "wPokedexWRAM0Scratch"
DEF TYPES_CURSOR EQUS "TYPES_STATE"
DEF TYPES_ORDINAL EQUS "TYPES_STATE + 1"
DEF TYPES_ROW EQUS "TYPES_STATE + 2"
DEF TYPES_COLUMN EQUS "TYPES_STATE + 3"
DEF TYPES_NEXT_SLOT EQUS "TYPES_STATE + 4"
DEF TYPES_PHASE EQUS "TYPES_STATE + 5"
DEF TYPES_FIRST_SLOT EQUS "TYPES_STATE + 6"
DEF TYPES_I_COUNT EQUS "TYPES_STATE + 7"
DEF TYPES_W_COUNT EQUS "TYPES_STATE + 8"
DEF TYPES_R_COUNT EQUS "TYPES_STATE + 9"
DEF TYPES_R_ROW EQUS "TYPES_STATE + 10"
DEF TYPES_W_LIST EQUS "TYPES_STATE + 11"
DEF TYPES_R_LIST EQUS "TYPES_STATE + 29"
DEF TYPES_X EQUS "TYPES_STATE + 47"
DEF TYPES_Y EQUS "TYPES_STATE + 48"
DEF TYPES_PAL EQUS "TYPES_STATE + 49"
DEF TYPES_PAGE EQUS "TYPES_STATE + 51"
DEF TYPES_LIST_COUNT EQUS "TYPES_STATE + 52"
DEF TYPES_LIST_ROW EQUS "TYPES_STATE + 53"
DEF TYPES_LIST_POINTER EQUS "TYPES_STATE + 54"
DEF TYPES_LIST_INDEX EQUS "TYPES_STATE + 56"
DEF TYPES_BADGE EQUS "TYPES_STATE + $40"
DEF TYPES_SHIFTED EQUS "TYPES_STATE + $80"
DEF TYPES_RASTER EQUS "TYPES_STATE + $100"
DEF TYPES_COLORS EQUS "TYPES_STATE + $1a0"
DEF TYPES_TOP_SLOTS EQUS "TYPES_STATE + $280"
DEF TYPES_I_LIST EQUS "TYPES_STATE + $2a0"
DEF TYPES_EFFECTS EQUS "TYPES_STATE + $300"
DEF TYPES_IDS EQUS "TYPES_STATE + $320"
DEF TYPES_PAGE_A EQUS "HIGH(TYPES_STATE + $200)"
DEF TYPES_PAGE_B EQUS "HIGH(TYPES_STATE + $400)"
DEF TYPES_CORNER EQU $28
DEF TYPES_SIDE EQU $29
DEF TYPES_DIVIDER EQU $2a
DEF TYPES_ARROW EQU $5a
DEF TYPES_ACTIVE EQUS "TYPES_STATE + $180"
DEF TYPES_SAVED_IE EQUS "TYPES_STATE + $181"
DEF TYPES_SAVED_STAT EQUS "TYPES_STATE + $182"
DEF TYPES_SAVED_LYC EQUS "TYPES_STATE + $183"
DEF TYPES_NEXT_LINE EQUS "TYPES_STATE + $184"
DEF TYPES_EVENT EQUS "TYPES_STATE + $185"
DEF TYPES_FRAME_READY EQUS "TYPES_STATE + $186"
DEF TYPES_PENDING EQUS "TYPES_STATE + $187"
DEF TYPES_EXIT EQUS "TYPES_STATE + $188"
ASSERT TYPES_SHIFTED + 8 tiles <= TYPES_RASTER
ASSERT TYPES_RASTER + 128 <= TYPES_ACTIVE
ASSERT TYPES_STATE + $189 <= TYPES_COLORS
ASSERT LOW(TYPES_RASTER) == 0
ASSERT LOW(TYPES_COLORS) == $a0
ASSERT TYPES_I_LIST + NUM_TYPES <= TYPES_EFFECTS
ASSERT TYPES_STATE + $460 <= POKEDEX_ORDER_SEEN_FLAGS
ASSERT NUM_TYPES == 18
ASSERT TypeMatchupsEnd - TypeMatchups <= 576

PokedexTypes_Initialize::
    farcall Pokedex_InitArrowCursor
	xor a
	ldh [hLCDCPointer], a
	ldh [hVBlank], a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	ldh [hSCX], a
	ldh [hSCY], a
	ldh [hWY], a
	ldh [hJoypadSum], a
	ld [wPokedexSelectedState], a
	ld [wPokedexOwnerTransition], a
	ld a, $a7
	ldh [hWX], a
	farcall Pokedex_CancelAnimationPrefetch
	call ClearSprites
	ld hl, TYPES_STATE
	ld bc, $460
	xor a
	call ByteFill
	ldh a, [rIE]
	ld [TYPES_SAVED_IE], a
	ldh a, [rSTAT]
	ld [TYPES_SAVED_STAT], a
	ldh a, [rLYC]
	ld [TYPES_SAVED_LYC], a
	ld hl, .Alphabetical
	ld de, TYPES_IDS
	ld bc, NUM_TYPES
	call CopyBytes
	ld a, TYPES_PAGE_A
	ld [TYPES_PAGE], a
	ldh [hLYOverrideStart], a
	call .RasterTable
	call .LoadGraphics
	call .LoadFrame
	call .LoadPalettes
	call .DrawShell
	call .DrawTop
IF DEF(TYPE_PANEL_PRECOMPUTED)
	call PokedexTypes_StageColours
	call PokedexTypes_LoadRecord
ELSE
	call PokedexTypes_CacheChart
	call PokedexTypes_DrawSelection
ENDC
	farcall Pokedex_StageOwnerTransitionMaps
.near_vblank
	ldh a, [rLY]
	cp 140
	jr c, .near_vblank
	cp 144
	jr nc, .near_vblank
	di
.vblank
	ldh a, [rLY]
	cp 144
	jr c, .vblank
	farcall PokedexResults_CommitBG
	call .HardwarePalettes
	call hTransferShadowOAM
	xor a
	ldh [hOAMUpdate], a
	ld a, DEXSTATE_TYPES_UPDATE
	ld [wJumptableIndex], a
	ld a, TRUE
	ld [TYPES_ACTIVE], a
	ld a, $ff
	ld [TYPES_NEXT_LINE], a
	ld a, VBLANK_POKEDEX | (1 << 4)
	ldh [hVBlank], a
	ld a, [TYPES_SAVED_IE]
	res B_IE_STAT, a
	ldh [rIE], a
	ei
	jp PokedexTypes_Update

.RasterTable:
	ld hl, .EventLines
	ld b, 11
	ld c, 8
.event
	ld a, [hli]
	push hl
	ld l, a
	ld h, HIGH(TYPES_RASTER)
	ld [hl], c
	pop hl
	ld a, c
	add 8
	ld c, a
	dec b
	jr nz, .event
	ret
.EventLines:
	db 7, 21, 35, 49, 63, 77, 95, 103, 111, 119, 127
.Alphabetical:
	db BUG, DARK, DRAGON, ELECTRIC, FAIRY, FIGHTING
	db FIRE, FLYING, GHOST, GRASS, GROUND, ICE
	db NORMAL, POISON, PSYCHIC_TYPE, ROCK, STEEL, WATER

.LoadGraphics:
	ld a, 1
	ldh [rVBK], a
	xor a
	ld [TYPES_ORDINAL], a
.base
	call .LoadBadge
	ld a, [TYPES_ORDINAL]
	add a
	add a
	ld c, a
	ld b, 4
	ld hl, TYPES_BADGE
	call .Upload
	ld a, [TYPES_ORDINAL]
	ld e, a
	ld d, 0
	ld hl, TYPES_TOP_SLOTS
	add hl, de
	ld a, e
	add a
	add a
	ld [hl], a
	call .LoadAccent
	ld hl, TYPES_ORDINAL
	inc [hl]
	ld a, [hl]
	cp NUM_TYPES
	jr c, .base
	ld a, 72
	ld [TYPES_NEXT_SLOT], a
	xor a
	ld [TYPES_ORDINAL], a
.shift
	call .OrdinalPosition
	ld a, [TYPES_ROW]
	ld e, a
	ld d, 0
	ld hl, .Phases
	add hl, de
	ld a, [hl]
	ld [TYPES_PHASE], a
	and a
	jr z, .next_shift
	call .LoadBadge
	call .ShiftBadge
	ld a, [TYPES_ORDINAL]
	ld e, a
	ld d, 0
	ld hl, TYPES_TOP_SLOTS
	add hl, de
	ld a, [TYPES_NEXT_SLOT]
	ld [hl], a
	ld c, a
	ld b, 8
	ld hl, TYPES_SHIFTED
	call .Upload
	ld a, [TYPES_NEXT_SLOT]
	add 8
	ld [TYPES_NEXT_SLOT], a
.next_shift
	ld hl, TYPES_ORDINAL
	inc [hl]
	ld a, [hl]
	cp NUM_TYPES
	jr c, .shift
	xor a
	ldh [rVBK], a
	ret
.Phases:
	db 0, 6, 4, 2, 0, 6
.TileRows:
	db 1, 2, 4, 6, 8, 9
.PixelRows:
	db 8, 22, 36, 50, 64, 78

.LoadBadge:
	ld a, [TYPES_ORDINAL]
	ld e, a
	ld d, 0
	ld hl, TYPES_IDS
	add hl, de
	ld a, [hl]
	ld e, a
	add a
	add e
	ld e, a
	ld hl, CompactTypeIconGFXPointers
	add hl, de
	ld a, BANK(CompactTypeIconGFXPointers)
	call GetFarByte
	push af
	inc hl
	ld a, BANK(CompactTypeIconGFXPointers)
	call GetFarWord
	ld de, TYPES_BADGE
	ld bc, 4 tiles
	pop af
	call FarCopyBytes
	; BG corners are gray, not transparent: color index 1 in every badge palette.
	ld hl, TYPES_BADGE
	set 7, [hl]
	ld hl, TYPES_BADGE + 14
	set 7, [hl]
	ld hl, TYPES_BADGE + 48
	set 0, [hl]
	ld hl, TYPES_BADGE + 62
	set 0, [hl]
	ret

.LoadAccent:
	ld a, [TYPES_ORDINAL]
	ld e, a
	ld d, 0
	ld hl, TYPES_IDS
	add hl, de
	ld a, [hl]
	add a
	ld e, a
	ld hl, TypeIconPalettePointers
	add hl, de
	ld a, BANK(TypeIconPalettePointers)
	call GetFarWord
	ld de, 4
	add hl, de
	push hl
	ld a, [TYPES_ORDINAL]
	add a
	add LOW(TYPES_COLORS)
	ld e, a
	ld d, HIGH(TYPES_COLORS)
	pop hl
	ld bc, 2
	ld a, BANK(TypeIconPalettes)
	jp FarCopyBytes

.ShiftBadge:
	ld hl, TYPES_SHIFTED
	ld b, 64
.gray
	ld [hl], $ff
	inc hl
	ld [hl], 0
	inc hl
	dec b
	jr nz, .gray
	xor a
	ld [TYPES_COLUMN], a
	ld hl, TYPES_BADGE
.column
	ld a, [TYPES_COLUMN]
	swap a
	ld e, a
	ld a, [TYPES_PHASE]
	add a
	add e
	add LOW(TYPES_SHIFTED)
	ld e, a
	ld d, HIGH(TYPES_SHIFTED)
	ld a, [TYPES_PHASE]
	ld b, a
	ld a, 8
	sub b
	add a
	ld c, a
	ld b, 0
	call CopyBytes
	ld a, [TYPES_COLUMN]
	swap a
	add LOW(TYPES_SHIFTED + 4 tiles)
	ld e, a
	ld d, HIGH(TYPES_SHIFTED + 4 tiles)
	ld a, [TYPES_PHASE]
	add a
	ld c, a
	ld b, 0
	call CopyBytes
	ld a, [TYPES_COLUMN]
	inc a
	ld [TYPES_COLUMN], a
	cp 4
	jr c, .column
	ret

.Upload:
	push bc
	push hl
	ld a, c
	call .TileID
	ld c, a
	swap a
	and $f
	ld d, a
	ld a, $90
	bit 7, c
	jr z, .unsigned
	ld a, $80
.unsigned
	add d
	ld d, a
	ld a, c
	swap a
	and $f0
	ld e, a
	pop hl
	call .TransferTile
	pop bc
	inc c
	dec b
	jr nz, .Upload
	ret

.TransferTile:
	push af
.wait
	ldh a, [rLY]
	cp 144
	jr nc, .try_vblank
	ldh a, [rSTAT]
	and 3
	cp 3
	jr nz, .wait
.fresh_hblank
	ldh a, [rSTAT]
	and 3
	cp 3
	jr z, .fresh_hblank
	and a
	jr nz, .wait
	jr .lock
.try_vblank
	cp 150
	jr nc, .wait
.lock
	di
	ldh a, [rSTAT]
	and 2
	jr z, .transfer
	ei
	jr .wait
.transfer
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	ldh [rVDMA_SRC_LOW], a
	ld a, d
	and $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, e
	ldh [rVDMA_DEST_LOW], a
	xor a
	ldh [rVDMA_LEN], a
	ei
	ld a, l
	add 1 tiles
	ld l, a
	jr nc, .advanced
	inc h
.advanced
	pop af
	ret

.TileID:
	push hl
	push de
	ld e, a
	ld d, 0
	ld hl, .Slots
	add hl, de
	ld a, [hl]
	pop de
	pop hl
	ret
.Slots:
FOR tile_id, $80, $b1
	db tile_id
ENDR
FOR tile_id, $33, $64
	db tile_id
ENDR
FOR tile_id, $d2, $fa
	db tile_id
ENDR
FOR tile_id, $00, $28
	db tile_id
ENDR
ASSERT @ - .Slots == 178

.OrdinalPosition:
	ld a, [TYPES_ORDINAL]
	ld b, 0
.divide
	cp 3
	jr c, .position
	sub 3
	inc b
	jr .divide
.position
	ld [TYPES_COLUMN], a
	ld a, b
	ld [TYPES_ROW], a
	ret

.LoadFrame:
	ld a, 1
	ldh [rVBK], a
	ld hl, PokedexMovesSearchLeftGFX
	ld de, TYPES_BADGE
	ld bc, 1 tiles
	ld a, BANK(PokedexMovesSearchLeftGFX)
	call FarCopyBytes
	ld hl, TYPES_BADGE
	; The shared junction's upper five rows sit outside this frame.
	ld b, 5
.corner_margin
	ld a, $ff
	ld [hli], a
	xor a
	ld [hli], a
	dec b
	jr nz, .corner_margin
	ld hl, TYPES_BADGE
	ld de, vTiles5 tile TYPES_CORNER
	call .TransferTile
	ld hl, TYPES_BADGE + 12
	ld a, [hli]
	ld c, a
	ld b, [hl]
	ld hl, TYPES_SHIFTED
	ld d, 8
.side
	ld a, c
	ld [hli], a
	ld a, b
	ld [hli], a
	dec d
	jr nz, .side
	ld hl, TYPES_SHIFTED
	ld de, vTiles5 tile TYPES_SIDE
	call .TransferTile
	ld hl, PokedexDescriptionGFX
	ld de, TYPES_BADGE
	ld bc, 1 tiles
	ld a, BANK(PokedexDescriptionGFX)
	call FarCopyBytes
	ld hl, TYPES_BADGE
	ld b, 16
.border_phase
	ld a, [hl]
	ld c, a
	rept 5
	add a
	endr
	bit 0, c
	jr z, .padding
	or $1f
.padding
	ld [hli], a
	dec b
	jr nz, .border_phase
	ld hl, TYPES_BADGE
	ld de, vTiles5 tile TYPES_DIVIDER
	call .TransferTile
	ld hl, Font + ('▶' - $80) * 8
	ld de, TYPES_BADGE
	ld bc, 8
	ld a, BANK(Font)
	call FarCopyBytes
	ld hl, TYPES_BADGE
	ld de, TYPES_SHIFTED
	ld b, 8
.arrow
	ld a, [hli]
	ld [de], a
	inc de
	xor a
	ld [de], a
	inc de
	dec b
	jr nz, .arrow
	ld hl, TYPES_SHIFTED
	ld de, vTiles3 tile TYPES_ARROW
	call .TransferTile
	xor a
	ldh [rVBK], a
	ret

.LoadPalettes:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rSVBK], a
	ld hl, PokedexUIPalette
	ld de, wBGPals1
	ld bc, 1 palettes
	ld a, BANK(PokedexUIPalette)
	call FarCopyBytes
	ld de, wBGPals1 palette 1
	ld b, 4
.badge_palette
	push bc
	ld hl, .BadgePalette
	ld bc, 1 palettes
	call CopyBytes
	pop bc
	dec b
	jr nz, .badge_palette
	ld hl, wBGPals1
	ld de, wBGPals2
	ld bc, 5 palettes
	call CopyBytes
	ld hl, .ArrowPalette
	ld de, wOBPals1
	ld bc, 1 palettes
	call CopyBytes
	ld hl, .ArrowPalette
	ld de, wOBPals2
	ld bc, 1 palettes
	call CopyBytes
	pop af
	ldh [rSVBK], a
	ret
.BadgePalette:
	RGB 31,31,31, 5,5,5, 0,0,0, 0,0,0
.ArrowPalette:
	RGB 0,0,0, 31,31,31, 31,31,31, 31,31,31

.HardwarePalettes:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rSVBK], a
	ld a, $80
	ldh [rBCPS], a
	ld hl, wBGPals1
	ld b, 5 palettes
.bg
	ld a, [hli]
	ldh [rBCPD], a
	dec b
	jr nz, .bg
	ld a, $80
	ldh [rOCPS], a
	ld hl, wOBPals1
	ld b, 1 palettes
.obj
	ld a, [hli]
	ldh [rOCPD], a
	dec b
	jr nz, .obj
	pop af
	ldh [rSVBK], a
	ret

.DrawShell:
	ld hl, wTilemap
	ld a, $32
	ld bc, SCREEN_AREA
	call ByteFill
	ld hl, wAttrmap
	xor a
	ld bc, SCREEN_AREA
	call ByteFill
	hlcoord 0, 0
	ld a, $34
	ld bc, SCREEN_WIDTH
	call ByteFill
	hlcoord 0, 11
	ld a, $74
	ld bc, SCREEN_WIDTH
	call ByteFill
	hlcoord 0, 17
	ld a, $39
	ld bc, SCREEN_WIDTH
	call ByteFill
	hlcoord 0, 0
	ld [hl], TYPES_CORNER
	hlcoord 19, 0
	ld [hl], TYPES_CORNER
	hlcoord 0, 17
	ld [hl], TYPES_CORNER
	hlcoord 19, 17
	ld [hl], TYPES_CORNER
	hlcoord 0, 0, wAttrmap
	ld [hl], BG_BANK1
	hlcoord 19, 0, wAttrmap
	ld [hl], BG_BANK1 | BG_XFLIP
	hlcoord 0, 17, wAttrmap
	ld [hl], BG_BANK1 | BG_YFLIP
	hlcoord 19, 17, wAttrmap
	ld [hl], BG_BANK1 | BG_XFLIP | BG_YFLIP
	ld b, 16
	hlcoord 0, 1
	decoord 0, 1, wAttrmap
.sides
	ld [hl], TYPES_SIDE
	ld a, BG_BANK1
	ld [de], a
	push hl
	push de
	ld a, l
	add 19
	ld l, a
	jr nc, .map_carry
	inc h
.map_carry
	ld a, e
	add 19
	ld e, a
	jr nc, .attr_carry
	inc d
.attr_carry
	ld [hl], TYPES_SIDE
	ld a, BG_BANK1 | BG_XFLIP
	ld [de], a
	pop de
	pop hl
	push bc
	ld bc, SCREEN_WIDTH
	add hl, bc
	ld a, e
	add SCREEN_WIDTH
	ld e, a
	jr nc, .next_side
	inc d
.next_side
	pop bc
	dec b
	jr nz, .sides
	hlcoord 0, 11
	ld [hl], TYPES_DIVIDER
	hlcoord 19, 11
	ld [hl], TYPES_DIVIDER
	ret

.DrawTop:
	xor a
	ld [TYPES_ORDINAL], a
.top
	call .OrdinalPosition
	ld a, [TYPES_ROW]
	ld e, a
	ld d, 0
	ld hl, .TileRows
	add hl, de
	ld a, [hl]
	ld [TYPES_Y], a
	ld hl, .Phases
	add hl, de
	ld a, [hl]
	ld [TYPES_PHASE], a
	ld a, [TYPES_COLUMN]
	inc a
	ld [TYPES_PAL], a
	dec a
	add a
	ld b, a
	add a
	add b
	add 2
	ld [TYPES_X], a
	ld a, [TYPES_ORDINAL]
	ld e, a
	ld d, 0
	ld hl, TYPES_TOP_SLOTS
	add hl, de
	ld a, [hl]
	ld [TYPES_FIRST_SLOT], a
	call .PlaceFour
	ld a, [TYPES_PHASE]
	and a
	jr z, .next_top
	ld hl, TYPES_Y
	inc [hl]
	ld a, [TYPES_FIRST_SLOT]
	add 4
	ld [TYPES_FIRST_SLOT], a
	call .PlaceFour
.next_top
	ld hl, TYPES_ORDINAL
	inc [hl]
	ld a, [hl]
	cp NUM_TYPES
	jr c, .top
	ret

.PlaceFour:
	ld a, [TYPES_Y]
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	ld e, l
	ld d, h
	add hl, hl
	add hl, hl
	add hl, de
	ld a, [TYPES_X]
	ld e, a
	ld d, 0
	add hl, de
	ld de, wTilemap
	add hl, de
	push hl
	ld de, wAttrmap - wTilemap
	add hl, de
	ld e, l
	ld d, h
	pop hl
	ld a, [TYPES_FIRST_SLOT]
	ld c, a
	ld b, 4
.cell
	ld a, c
	call .TileID
	ld [hli], a
	ld a, [TYPES_PAL]
	or BG_BANK1
	ld [de], a
	inc de
	inc c
	dec b
	jr nz, .cell
	ret

PokedexTypes_DrawSelection::
	call PokedexTypes_BuildMatchups
	call PokedexTypes_StageColours
	ld a, $32
	hlcoord 1, 12
	lb bc, 5, 18
	call .ClearLower
	xor a
	hlcoord 1, 12, wAttrmap
	lb bc, 5, 18
	call .ClearLower
	ld a, 'W'
	ld b, 12
	call .Label
	ld a, [TYPES_R_ROW]
	ld b, a
	ld a, 'R'
	call .Label
	ld a, [TYPES_I_COUNT]
	and a
	jr z, .lists
	ld a, 'I'
	ld b, 16
	call .Label
.lists
	ld hl, TYPES_W_LIST
	ld a, [TYPES_W_COUNT]
	ld c, a
	ld b, 12
	call .DrawList
	ld hl, TYPES_R_LIST
	ld a, [TYPES_R_COUNT]
	ld c, a
	ld a, [TYPES_R_ROW]
	ld b, a
	call .DrawList
	ld hl, TYPES_I_LIST
	ld a, [TYPES_I_COUNT]
	ld c, a
	ld b, 16
	call .DrawList
	jp .Cursor

.Label:
	push af
	hlcoord 1, 0
	ld de, SCREEN_WIDTH
.label_row
	add hl, de
	dec b
	jr nz, .label_row
	pop af
	ld [hli], a
	ld [hl], ':'
	ret

.ClearLower:
	push af
	push bc
	push hl
	ld b, 0
	call PokedexTypes_Fill
	pop hl
	ld de, SCREEN_WIDTH
	add hl, de
	pop bc
	pop af
	dec b
	jr nz, .ClearLower
	ret

.DrawList:
	ld a, c
	ld [TYPES_LIST_COUNT], a
	and a
	ret z
	ld a, b
	ld [TYPES_LIST_ROW], a
	ld a, l
	ld [TYPES_LIST_POINTER], a
	ld a, h
	ld [TYPES_LIST_POINTER + 1], a
	xor a
	ld [TYPES_LIST_INDEX], a
.list
	call PokedexTypes_Yield
	ld a, [TYPES_LIST_INDEX]
	ld e, a
	ld d, 0
	ld a, [TYPES_LIST_POINTER]
	ld l, a
	ld a, [TYPES_LIST_POINTER + 1]
	ld h, a
	add hl, de
	ld a, [hl]
	ld [TYPES_ORDINAL], a
	add a
	add a
	ld [TYPES_FIRST_SLOT], a
	ld a, [TYPES_LIST_INDEX]
	and 3
	ld [TYPES_COLUMN], a
	inc a
	ld [TYPES_PAL], a
	dec a
	add a
	add a
	add 3
	ld [TYPES_X], a
	ld a, [TYPES_LIST_INDEX]
	srl a
	srl a
	ld b, a
	ld a, [TYPES_LIST_ROW]
	add b
	ld [TYPES_Y], a
	call PokedexTypes_Initialize.PlaceFour
	ld a, [TYPES_Y]
	sub 5
	ld c, a
	ld a, [TYPES_COLUMN]
	ld d, a
	ld a, [TYPES_ORDINAL]
	call PokedexTypes_StoreColour
	ld hl, TYPES_LIST_INDEX
	inc [hl]
	ld a, [TYPES_LIST_COUNT]
	cp [hl]
	jr nz, .list
	ret

.Cursor:
	ld a, [TYPES_CURSOR]
	ld [TYPES_ORDINAL], a
	call PokedexTypes_Initialize.OrdinalPosition
	ld a, [TYPES_ROW]
	ld e, a
	ld d, 0
	ld hl, PokedexTypes_Initialize.PixelRows
	add hl, de
	ld a, [hl]
	add 16
	ld [wShadowOAM], a
	ld a, [TYPES_COLUMN]
	ld b, a
	add a
	add b
	swap a
	add 16
	ld [wShadowOAM + 1], a
	ld a, TYPES_ARROW
	ld [wShadowOAM + 2], a
	ld a, OAM_BANK1
	ld [wShadowOAM + 3], a
	ret

; Build one defensive result from the canonical battle chart, including records
; after the Foresight divider. Battle-only modifiers are deliberately excluded.
PokedexTypes_BuildMatchups::
	ld hl, TYPES_EFFECTS
	ld bc, 29
	ld a, EFFECTIVE
	call PokedexTypes_Fill
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoGFX)
	ldh [rSVBK], a
	ld a, [TYPES_CURSOR]
	ld e, a
	ld d, 0
	ld hl, TYPES_IDS
	add hl, de
	ld d, [hl]
	ld hl, wPokedexInfoGFX
.record
	call PokedexTypes_Yield
	ld a, [hli]
	cp -1
	jr z, .lists
	cp -2
	jr z, .record
	ld b, a
	ld a, [hli]
	ld c, a
	ld a, [hli]
	ld e, a
	ld a, c
	cp d
	jr nz, .record
	push hl
	ld l, b
	ld h, HIGH(TYPES_EFFECTS)
	ld [hl], e
	pop hl
	jr .record
.lists
	pop af
	ldh [rSVBK], a
	xor a
	ld [TYPES_I_COUNT], a
	ld [TYPES_W_COUNT], a
	ld [TYPES_R_COUNT], a
	ld [TYPES_ORDINAL], a
.type
	call PokedexTypes_Yield
	ld a, [TYPES_ORDINAL]
	ld e, a
	ld d, 0
	ld hl, TYPES_IDS
	add hl, de
	ld l, [hl]
	ld h, HIGH(TYPES_EFFECTS)
	ld a, [hl]
	cp SUPER_EFFECTIVE
	jr z, .weak
	cp EFFECTIVE
	jr nc, .next
	and a
	jr nz, .resist
	; Steel keeps its compact combined resistance/immunity list.
	ld a, [TYPES_CURSOR]
	ld e, a
	ld d, 0
	ld hl, TYPES_IDS
	add hl, de
	ld a, [hl]
	cp STEEL
	jr z, .resist
	ld hl, TYPES_I_COUNT
	ld de, TYPES_I_LIST
	jr .append
.resist
	ld hl, TYPES_R_COUNT
	ld de, TYPES_R_LIST
	jr .append
.weak
	ld hl, TYPES_W_COUNT
	ld de, TYPES_W_LIST
.append
	ld a, [hl]
	inc [hl]
	ld l, a
	ld h, 0
	add hl, de
	ld a, [TYPES_ORDINAL]
	ld [hl], a
.next
	ld hl, TYPES_ORDINAL
	inc [hl]
	ld a, [hl]
	cp NUM_TYPES
	jr c, .type
	ld a, [TYPES_W_COUNT]
	cp 5
	ld a, 14
	jr c, .r_row
	inc a
.r_row
	ld [TYPES_R_ROW], a
	ret

PokedexTypes_StageColours::
	ld a, [TYPES_PAGE]
	ld h, a
	ld l, 0
	ld bc, 96
	xor a
	call PokedexTypes_Fill
	xor a
	ld [TYPES_ORDINAL], a
.top
	call PokedexTypes_Yield
	call PokedexTypes_Initialize.OrdinalPosition
	ld a, [TYPES_ROW]
	inc a
	ld c, a
	ld a, [TYPES_COLUMN]
	ld d, a
	ld a, [TYPES_ORDINAL]
	call PokedexTypes_StoreColour
	ld hl, TYPES_ORDINAL
	inc [hl]
	ld a, [hl]
	cp NUM_TYPES
	jr c, .top
	ret

PokedexTypes_StoreColour::
	push bc
	push de
	push hl
	add a
	add LOW(TYPES_COLORS)
	ld l, a
	ld h, HIGH(TYPES_COLORS)
	ld b, [hl]
	inc hl
	ld e, [hl]
	ld a, d
	add a
	ld d, a
	ld a, c
	add a
	add a
	add a
	add d
	ld l, a
	ld a, [TYPES_PAGE]
	ld h, a
	ld [hl], b
	inc hl
	ld [hl], e
	pop hl
	pop de
	pop bc
	ret

PokedexTypes_Update::
.owner_loop
	call PokedexTypes_Yield
	ld a, [TYPES_FRAME_READY]
	and a
	jr z, .owner_loop
	xor a
	ld [TYPES_FRAME_READY], a
	call JoyTextDelay
	call PokedexTypes_BlinkCursor
	; Only VBlank accumulates edges, so this short exchange cannot delay a
	; raster palette write beyond HBlank's available time.
	di
	ldh a, [hJoypadSum]
	ld b, a
	xor a
	ldh [hJoypadSum], a
	ei
	ldh a, [hJoyPressed]
	or b
	and PAD_B | PAD_SELECT
	jp nz, PokedexTypes_Leave
	ld a, b
	and PAD_CTRL_PAD
	jr nz, .direction
	ldh a, [hJoyLast]
	and PAD_CTRL_PAD
	jr z, .owner_loop
.direction
	ld c, a
	ld a, [TYPES_CURSOR]
	ld [TYPES_ORDINAL], a
	call PokedexTypes_Initialize.OrdinalPosition
	bit B_PAD_UP, c
	jr nz, .up
	bit B_PAD_DOWN, c
	jr nz, .down
	bit B_PAD_LEFT, c
	jr nz, .left
	ld hl, TYPES_COLUMN
	inc [hl]
	ld a, [hl]
	cp 3
	jr c, .move
	ld [hl], 0
	jr .move
.left
	ld hl, TYPES_COLUMN
	ld a, [hl]
	and a
	jr nz, .left_step
	ld [hl], 3
.left_step
	dec [hl]
	jr .move
.up
	ld hl, TYPES_ROW
	ld a, [hl]
	and a
	jr nz, .up_step
	ld [hl], 6
.up_step
	dec [hl]
	jr .move
.down
	ld hl, TYPES_ROW
	inc [hl]
	ld a, [hl]
	cp 6
	jr c, .move
	ld [hl], 0
.move
	farcall Pokedex_ResetArrowCursorBlink
	ld a, [TYPES_ROW]
	ld b, a
	add a
	add b
	ld b, a
	ld a, [TYPES_COLUMN]
	add b
	ld [TYPES_CURSOR], a
	ld a, TRUE
	ldh [hOAMUpdate], a
	ldh a, [hLYOverrideStart]
	xor TYPES_PAGE_A ^ TYPES_PAGE_B
	ld [TYPES_PAGE], a
	call PokedexTypes_PrepareLower
	ld a, TRUE
	ld [TYPES_PENDING], a
.publication
	call PokedexTypes_Yield
	ld a, [TYPES_PENDING]
	and a
	jr nz, .publication
	jp .owner_loop

PokedexTypes_BlinkCursor:
	farcall Pokedex_AdvanceArrowCursorBlink
	jr z, .visible
	xor a
	ld [wShadowOAM], a
	ret
.visible
	jp PokedexTypes_DrawSelection.Cursor

PokedexTypes_CommitLower:
	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexOwnerAttrmapBuffer + 12 * TILEMAP_WIDTH
	call .Transfer
	xor a
	ldh [rVBK], a
	ld hl, wPokedexOwnerTilemapBuffer + 12 * TILEMAP_WIDTH
	call .Transfer
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ret
.Transfer:
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	ldh [rVDMA_SRC_LOW], a
	ld a, HIGH(vBGMap0 + 12 * TILEMAP_WIDTH) & $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, LOW(vBGMap0 + 12 * TILEMAP_WIDTH)
	ldh [rVDMA_DEST_LOW], a
	ld a, 2 * 5 - 1
	ldh [rVDMA_LEN], a
	ret
PokedexTypes_Leave:
	ld a, TRUE
	ld [TYPES_EXIT], a
.mask
	call PokedexTypes_Yield
	ld a, [TYPES_ACTIVE]
	and a
	jr nz, .mask
	di
	ld a, [TYPES_SAVED_STAT]
	ldh [rSTAT], a
	ld a, [TYPES_SAVED_LYC]
	ldh [rLYC], a
	ldh a, [rIF]
	res B_IF_STAT, a
	ldh [rIF], a
	ld a, [TYPES_SAVED_IE]
	ldh [rIE], a
	ei
	xor a
	ldh [hLCDCPointer], a
	ldh [hLYOverrideStart], a
	farcall Pokedex_InitGridCacheState
	farcall PokedexListing_BeginMenuTransition
	ld a, DEXSELECT_STATE_TYPES_RETURN
	ld [wPokedexSelectedState], a
	ld a, DEXSTATE_OPTION_SCR
	ld [wJumptableIndex], a
	ret
