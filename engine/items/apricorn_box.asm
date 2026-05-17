DEF APRICORN_BOX_RED_TILE    EQU $00
DEF APRICORN_BOX_BLUE_TILE   EQU $09
DEF APRICORN_BOX_YELLOW_TILE EQU $12
DEF APRICORN_BOX_GREEN_TILE  EQU $1b
DEF APRICORN_BOX_WHITE_TILE  EQU $25
DEF APRICORN_BOX_BLACK_TILE  EQU $2e
DEF APRICORN_BOX_EMPTY_TILE  EQU $37
DEF APRICORN_BOX_ITEMS_TILE  EQU $40
DEF APRICORN_BOX_TITLE_TILE  EQU $49
DEF APRICORN_BOX_PINK_TILE   EQU $55
DEF APRICORN_BOX_HEADER_TILE EQU $5e
DEF APRICORN_BOX_BORDER_TILE EQU $24

ApricornBox:
	xor a
	ld [wMenuCursorPosition], a
	call ApricornBox_InitGFX
	call ApricornBox_UpdateSelection
	call ApricornBox_TransferTilemapAndAttrmap
	call ApricornBox_LoadColors

.loop
	call DelayFrame
	call JoyTextDelay
	ldh a, [hJoyPressed]
	bit B_PAD_A, a
	jr nz, .a_button
	bit B_PAD_B, a
	jr nz, .quit
	ldh a, [hJoyLast]
	bit B_PAD_LEFT, a
	jr nz, .left
	bit B_PAD_RIGHT, a
	jr nz, .right
	jr .loop

.left
	ld hl, .LeftMoves
	jr .move

.right
	ld hl, .RightMoves

.move
	ld a, [wMenuCursorPosition]
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [hl]
	ld [wMenuCursorPosition], a
	call ApricornBox_DrawApricorns
	call ApricornBox_UpdateSelection
	call ApricornBox_TransferTilemapAndAttrmap
	jr .loop

.a_button
	call ApricornBox_ItemMenu
	call ApricornBox_DrawLayout
	call ApricornBox_UpdateSelection
	call ApricornBox_TransferTilemapAndAttrmap
	jr .loop

.quit
	ld a, PAD_B
	call MenuClickSound
	call ClearSprites
	xor a
	ldh [hBGMapMode], a
	farcall Pack_InitGFX_NoColors
	farcall WaitBGMap_DrawPackGFX
	farcall Pack_InitColors
	ret

.LeftMoves:
	db 6, 0, 1, 2, 3, 4, 5
.RightMoves:
	db 1, 2, 3, 4, 5, 6, 0

ApricornBox_TransferTilemapAndAttrmap:
	ldh a, [hCGB]
	and a
	jr z, .transfer
	call ApricornBox_BufferBlackWhiteApricorns

.transfer
	call HDMATransferTilemapAndAttrmap_Menu
	xor a
	ldh [hBGMapMode], a
	ret

ApricornBox_BufferBlackWhiteApricorns:
	ld hl, ApricornBoxBlackWhiteBGMapPointers
	ld de, wBGMapBufferPointers
	ld bc, ApricornBoxBlackWhiteBGMapPointers.End - ApricornBoxBlackWhiteBGMapPointers
	call CopyBytes

	hlcoord 10, 2
	ld de, wBGMapBuffer
	call ApricornBox_CopyBlackWhiteRows

	hlcoord 10, 2, wAttrmap
	ld de, wBGMapPalBuffer
	call ApricornBox_CopyBlackWhiteRows

	ld a, 12
	ldh [hBGMapTileCount], a
	ld a, TRUE
	ldh [hBGMapUpdate], a
	ret

ApricornBox_CopyBlackWhiteRows:
	ld b, 3
.row
	ld c, 8
.column
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .column
	push de
	ld de, SCREEN_WIDTH - 8
	add hl, de
	pop de
	dec b
	jr nz, .row
	ret

ApricornBoxBlackWhiteBGMapPointers:
	dw vBGMap0 + 2 * TILEMAP_WIDTH + 10
	dw vBGMap0 + 2 * TILEMAP_WIDTH + 12
	dw vBGMap0 + 2 * TILEMAP_WIDTH + 14
	dw vBGMap0 + 2 * TILEMAP_WIDTH + 16
	dw vBGMap0 + 3 * TILEMAP_WIDTH + 10
	dw vBGMap0 + 3 * TILEMAP_WIDTH + 12
	dw vBGMap0 + 3 * TILEMAP_WIDTH + 14
	dw vBGMap0 + 3 * TILEMAP_WIDTH + 16
	dw vBGMap0 + 4 * TILEMAP_WIDTH + 10
	dw vBGMap0 + 4 * TILEMAP_WIDTH + 12
	dw vBGMap0 + 4 * TILEMAP_WIDTH + 14
	dw vBGMap0 + 4 * TILEMAP_WIDTH + 16
.End

ApricornBox_ItemMenu:
	ld a, [wMenuCursorPosition]
	ld [wMenuCursorPositionBackup], a
	call ApricornBox_SetSelectedItemAndQuantity
	jr z, .no_apricorns
	ld a, PAD_A
	call MenuClickSound
	ld hl, ApricornBoxTossMenuHeader
	call LoadMenuHeader
	call VerticalMenu
	push af
	ld a, [wMenuCursorY]
	ld b, a
	push bc
	call ExitMenu
	pop bc
	pop af
	jr c, .done
	ld a, b
	dec a
	jr nz, .done
	call ApricornBox_TossSelectedApricorn
.done
	ld a, [wMenuCursorPositionBackup]
	ld [wMenuCursorPosition], a
	ret

.no_apricorns
	ld a, [wMenuCursorPositionBackup]
	ld [wMenuCursorPosition], a
	ld de, SFX_WRONG
	jp PlaySFX

ApricornBox_TossSelectedApricorn:
	ld hl, ApricornBoxAskThrowAwayText
	call ApricornBox_PrintTextNoScroll
	farcall SelectQuantityToToss
	push af
	call ExitMenu
	pop af
	jr c, .done
	call ApricornBox_GetCurItemName
	ld hl, ApricornBoxAskQuantityThrowAwayText
	call MenuTextbox
	call YesNoBox
	push af
	call ExitMenu
	pop af
	jr c, .done
	ld hl, wNumItems
	ld a, [wCurItemQuantity]
	call TossItem
	call ApricornBox_GetCurItemName
	ld hl, ApricornBoxThrewAwayText
	call ApricornBox_PrintTextNoScroll
.done
	ret

ApricornBox_PrintTextNoScroll:
	ld a, [wOptions]
	push af
	set NO_TEXT_SCROLL, a
	ld [wOptions], a
	call PrintText
	pop af
	ld [wOptions], a
	ret

ApricornBox_SetSelectedItemAndQuantity:
	call ApricornBox_GetSelectedItemID
	ld [wCurItem], a
	call ApricornBox_GetSelectedQuantity
	ld a, [wItemQuantityChange]
	ld [wItemQuantity], a
	ld [wCurItemQuantity], a
	and a
	ret

ApricornBox_GetSelectedItemName:
	call ApricornBox_GetSelectedItemID
	ld [wCurItem], a

ApricornBox_GetCurItemName:
	ld a, [wCurItem]
	ld [wNamedObjectIndex], a
	call GetItemName
	jp CopyName1

ApricornBox_GetSelectedItemID:
	ld hl, ApricornBoxItemIDs
	ld a, [wMenuCursorPosition]
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [hl]
	ret

ApricornBox_InitGFX:
	xor a
	ldh [hBGMapMode], a
	call ClearBGPalettes
	call ClearSprites
	call DisableLCD
	call ClearTilemap
	call ApricornBox_ClearAttrmap
	call ApricornBox_LoadGFX
	call ApricornBox_DrawLayout
	call EnableLCD
	ret

ApricornBox_ClearAttrmap:
	hlcoord 0, 0, wAttrmap
	ld bc, wAttrmapEnd - wAttrmap
	xor a
	jp ByteFill

ApricornBox_LoadGFX:
	ld hl, PackMenuGFX
	ld de, vTiles2
	ld bc, $60 tiles
	ld a, BANK(PackMenuGFX)
	call FarCopyBytes

	ld hl, ApricornBoxRedApricornGFX
	ld de, vTiles2 tile APRICORN_BOX_RED_TILE
	ld bc, 9 tiles
	ld a, BANK(ApricornBoxRedApricornGFX)
	call FarCopyBytes

	ld hl, ApricornBoxBlueApricornGFX
	ld de, vTiles2 tile APRICORN_BOX_BLUE_TILE
	ld bc, 9 tiles
	ld a, BANK(ApricornBoxBlueApricornGFX)
	call FarCopyBytes

	ld hl, ApricornBoxYellowApricornGFX
	ld de, vTiles2 tile APRICORN_BOX_YELLOW_TILE
	ld bc, 9 tiles
	ld a, BANK(ApricornBoxYellowApricornGFX)
	call FarCopyBytes

	ld hl, ApricornBoxGreenApricornGFX
	ld de, vTiles2 tile APRICORN_BOX_GREEN_TILE
	ld bc, 9 tiles
	ld a, BANK(ApricornBoxGreenApricornGFX)
	call FarCopyBytes

	ld hl, ApricornBoxWhiteApricornGFX
	ld de, vTiles2 tile APRICORN_BOX_WHITE_TILE
	ld bc, 9 tiles
	ld a, BANK(ApricornBoxWhiteApricornGFX)
	call FarCopyBytes

	ld hl, ApricornBoxBlackApricornGFX
	ld de, vTiles2 tile APRICORN_BOX_BLACK_TILE
	ld bc, 9 tiles
	ld a, BANK(ApricornBoxBlackApricornGFX)
	call FarCopyBytes
	ld hl, vTiles2 tile APRICORN_BOX_BLACK_TILE
	call ApricornBox_MergeColor2IntoColor3

	ld hl, ApricornBoxRedApricornGFX
	ld de, vTiles2 tile APRICORN_BOX_EMPTY_TILE
	ld bc, 9 tiles
	ld a, BANK(ApricornBoxRedApricornGFX)
	call FarCopyBytes

	ld hl, ApricornBoxPinkApricornGFX
	ld de, vTiles2 tile APRICORN_BOX_PINK_TILE
	ld bc, 9 tiles
	ld a, BANK(ApricornBoxPinkApricornGFX)
	call FarCopyBytes

	ld hl, ApricornBoxTitleGFX
	ld de, vTiles2 tile APRICORN_BOX_TITLE_TILE
	ld bc, 12 tiles
	ld a, BANK(ApricornBoxTitleGFX)
	call FarCopyBytes

	ld hl, ApricornBoxHeaderGFX
	ld de, vTiles2 tile APRICORN_BOX_HEADER_TILE
	ld bc, 1 tiles
	ld a, BANK(ApricornBoxHeaderGFX)
	jp FarCopyBytes

ApricornBox_MergeColor2IntoColor3:
	ld b, 9 * TILE_WIDTH
.loop
	ld a, [hli]
	or [hl]
	dec hl
	ld [hli], a
	inc hl
	dec b
	jr nz, .loop
	ret

ApricornBox_DrawLayout:
	hlcoord 0, 0
	lb bc, 2, SCREEN_WIDTH
	ld a, APRICORN_BOX_HEADER_TILE
	call FillBoxWithByte

	hlcoord 0, 2
	lb bc, 10, 2
	ld a, APRICORN_BOX_BORDER_TILE
	call FillBoxWithByte
	hlcoord 18, 2
	lb bc, 10, 2
	ld a, APRICORN_BOX_BORDER_TILE
	call FillBoxWithByte

	hlcoord 0, 2, wAttrmap
	lb bc, 10, 2
	ld a, 1
	call FillBoxWithByte
	hlcoord 18, 2, wAttrmap
	lb bc, 10, 2
	ld a, 1
	call FillBoxWithByte

	hlcoord 7, 0
	lb bc, 2, 6
	ld a, APRICORN_BOX_TITLE_TILE
	call ApricornBox_PlaceTileBlock

	hlcoord 14, 1
	ld a, APRICORN_BOX_ITEMS_TILE
	ld c, 5
.items_loop
	ld [hli], a
	inc a
	dec c
	jr nz, .items_loop

	call ApricornBox_DrawApricorns
	jp ApricornBox_DrawTextboxes

ApricornBox_DrawApricorns:
	hlcoord 3, 2
	lb bc, 3, 3
	ld a, APRICORN_BOX_RED_TILE
	call ApricornBox_PlaceTileBlock
	hlcoord 3, 2, wAttrmap
	lb bc, 3, 3
	ld de, wRedApricornQuantity
	ld a, 4
	call ApricornBox_FillApricornAttr

	hlcoord 7, 2
	lb bc, 3, 3
	ld a, APRICORN_BOX_BLUE_TILE
	call ApricornBox_PlaceTileBlock
	hlcoord 7, 2, wAttrmap
	lb bc, 3, 3
	ld de, wBluApricornQuantity
	ld a, 2
	call ApricornBox_FillApricornAttr

	hlcoord 11, 2
	lb bc, 3, 3
	ld a, APRICORN_BOX_WHITE_TILE
	ld de, wWhtApricornQuantity
	call ApricornBox_PlaceMaybeEmptyApricornTiles
	hlcoord 11, 2, wAttrmap
	lb bc, 3, 3
	ld de, wWhtApricornQuantity
	ld a, 7
	call ApricornBox_FillApricornAttr

	hlcoord 15, 2
	lb bc, 3, 3
	ld a, APRICORN_BOX_BLACK_TILE
	ld de, wBlkApricornQuantity
	call ApricornBox_PlaceMaybeEmptyApricornTiles
	hlcoord 15, 2, wAttrmap
	lb bc, 3, 3
	ld de, wBlkApricornQuantity
	ld a, 7
	call ApricornBox_FillApricornAttr

	hlcoord 5, 5
	lb bc, 3, 3
	ld a, APRICORN_BOX_YELLOW_TILE
	call ApricornBox_PlaceTileBlock
	hlcoord 5, 5, wAttrmap
	lb bc, 3, 3
	ld de, wYlwApricornQuantity
	ld a, 5
	call ApricornBox_FillApricornAttr

	hlcoord 9, 5
	lb bc, 3, 3
	ld a, APRICORN_BOX_GREEN_TILE
	call ApricornBox_PlaceTileBlock
	hlcoord 9, 5, wAttrmap
	lb bc, 3, 3
	ld de, wGrnApricornQuantity
	ld a, 3
	call ApricornBox_FillApricornAttr

	hlcoord 13, 5
	lb bc, 3, 3
	ld a, APRICORN_BOX_PINK_TILE
	call ApricornBox_PlaceTileBlock
	hlcoord 13, 5, wAttrmap
	lb bc, 3, 3
	ld de, wPnkApricornQuantity
	ld a, 6
	jp ApricornBox_FillApricornAttr

ApricornBox_PlaceMaybeEmptyApricornTiles:
	push af
	push hl
	push bc
	call ApricornBox_IsSelectedQuantity
	pop bc
	pop hl
	jr c, .normal
	ld a, [de]
	and a
	jr nz, .normal
	pop af
	ld a, APRICORN_BOX_EMPTY_TILE
	jp ApricornBox_PlaceTileBlock

.normal
	pop af
	jp ApricornBox_PlaceTileBlock

ApricornBox_FillApricornAttr:
	push af
	push hl
	push bc
	call ApricornBox_IsSelectedQuantity
	pop bc
	pop hl
	jr c, .has_any
	ld a, [de]
	and a
	jr nz, .has_any
	pop af
	xor a
	jp FillBoxWithByte

.has_any
	pop af
	jp FillBoxWithByte

ApricornBox_IsSelectedQuantity:
	push de
	ld hl, ApricornBoxQuantityPointers
	ld a, [wMenuCursorPosition]
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop de
	ld a, e
	cp l
	jr nz, .no
	ld a, d
	cp h
	jr nz, .no
	scf
	ret

.no
	and a
	ret

ApricornBox_DrawTextboxes:
	hlcoord 2, 8
	lb bc, 2, 14
	call Textbox
	hlcoord 2, 8, wAttrmap
	lb bc, 4, 16
	xor a
	call FillBoxWithByte

	hlcoord 0, 12
	lb bc, 4, 18
	call Textbox
	hlcoord 0, 12, wAttrmap
	lb bc, 6, 20
	xor a
	jp FillBoxWithByte

ApricornBox_PlaceTileBlock:
.row
	push bc
	push hl
.column
	ld [hli], a
	inc a
	dec c
	jr nz, .column
	pop hl
	ld de, SCREEN_WIDTH
	add hl, de
	pop bc
	dec b
	jr nz, .row
	ret

ApricornBox_LoadColors:
	ldh a, [hCGB]
	and a
	jr nz, .cgb
	jp SetDefaultBGPAndOBP

.cgb
	ld hl, ApricornBoxPalettes
	ld de, wBGPals1
	ld bc, 8 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	ld hl, ApricornBoxCursorPalette
	ld de, wOBPals1 palette 0
	ld bc, 1 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM
	farcall ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

ApricornBox_UpdateSelection:
	call ApricornBox_DrawTextboxes
	call ApricornBox_PlaceCursor
	call ApricornBox_GetSelectedQuantity

	call ApricornBox_GetSelectedColorName
	hlcoord 3, 9
	call PlaceString

	hlcoord 3, 10
	ld de, ApricornBoxQuantityLabel
	call PlaceString
	ld h, b
	ld l, c
	ld de, wItemQuantityChange
	lb bc, PRINTNUM_LEADINGZEROS | 1, 2
	call PrintNum

	hlcoord 1, 14
	ld de, ApricornBoxBallLeadText
	call PlaceString

	call ApricornBox_GetSelectedBallName
	hlcoord 1, 16
	jp PlaceString

ApricornBox_GetSelectedColorName:
	ld hl, ApricornBoxColorNamePointers
	jr ApricornBox_GetSelectedString

ApricornBox_GetSelectedBallName:
	ld hl, ApricornBoxBallNamePointers

ApricornBox_GetSelectedString:
	ld a, [wMenuCursorPosition]
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ret

ApricornBox_GetSelectedQuantity:
	ld hl, ApricornBoxQuantityPointers
	ld a, [wMenuCursorPosition]
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [hl]
	ld [wItemQuantityChange], a
	ret

ApricornBox_PlaceCursor:
	ld hl, ApricornBoxCursorPositions
	ld a, [wMenuCursorPosition]
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld a, [hli]
	add 8
	ld [wShadowOAMSprite00XCoord], a
	ld a, [hl]
	add 16
	ld [wShadowOAMSprite00YCoord], a
	ld a, '▶'
	ld [wShadowOAMSprite00TileID], a
	xor a
	ld [wShadowOAMSprite00Attributes], a
	ret

ApricornBoxColorNamePointers:
	dw .Red
	dw .Blue
	dw .White
	dw .Black
	dw .Yellow
	dw .Green
	dw .Pink

.Red:    db "RED@"
.Blue:   db "BLUE@"
.White:  db "WHITE@"
.Black:  db "BLACK@"
.Yellow: db "YELLOW@"
.Green:  db "GREEN@"
.Pink:   db "PINK@"

ApricornBoxBallNamePointers:
	dw .Level
	dw .Lure
	dw .Fast
	dw .Heavy
	dw .Moon
	dw .Friend
	dw .Love

.Level:  db "LEVEL BALL.@"
.Lure:   db "LURE BALL.@"
.Fast:   db "FAST BALL.@"
.Heavy:  db "HEAVY BALL.@"
.Moon:   db "MOON BALL.@"
.Friend: db "FRIEND BALL.@"
.Love:   db "LOVE BALL.@"

ApricornBoxItemIDs:
	db RED_APRICORN
	db BLU_APRICORN
	db WHT_APRICORN
	db BLK_APRICORN
	db YLW_APRICORN
	db GRN_APRICORN
	db PNK_APRICORN

ApricornBoxQuantityPointers:
	dw wRedApricornQuantity
	dw wBluApricornQuantity
	dw wWhtApricornQuantity
	dw wBlkApricornQuantity
	dw wYlwApricornQuantity
	dw wGrnApricornQuantity
	dw wPnkApricornQuantity

ApricornBoxCursorPositions:
	db 17, 24
	db 49, 24
	db 81, 24
	db 113, 24
	db 33, 48
	db 65, 48
	db 97, 48

ApricornBoxQuantityLabel:
	db "APRICORN  ×@"

ApricornBoxBallLeadText:
	db "Can be made into a@"

ApricornBoxTossMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 7, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 2 ; items
	db "TOSS@"
	db "QUIT@"

ApricornBoxAskThrowAwayText:
	text_far _AskThrowAwayText
	text_end

ApricornBoxAskQuantityThrowAwayText:
	text_far _AskQuantityThrowAwayText
	text_end

ApricornBoxThrewAwayText:
	text_far _ThrewAwayText
	text_end

ApricornBoxPalettes:
INCLUDE "gfx/items/apricorns/apricorn_box.pal.asm"

ApricornBoxCursorPalette:
	RGB 31, 31, 31
	RGB 21, 21, 21
	RGB 10, 10, 10
	RGB 00, 00, 00

ApricornBoxRedApricornGFX:
INCBIN "gfx/items/apricorns/red_apricorn.2bpp"
ApricornBoxBlueApricornGFX:
INCBIN "gfx/items/apricorns/blue_apricorn.2bpp"
ApricornBoxYellowApricornGFX:
INCBIN "gfx/items/apricorns/yellow_apricorn.2bpp"
ApricornBoxGreenApricornGFX:
INCBIN "gfx/items/apricorns/green_apricorn.2bpp"
ApricornBoxWhiteApricornGFX:
INCBIN "gfx/items/apricorns/white_apricorn.2bpp"
ApricornBoxBlackApricornGFX:
INCBIN "gfx/items/apricorns/black_apricorn.2bpp"
ApricornBoxPinkApricornGFX:
INCBIN "gfx/items/apricorns/pink_apricorn.2bpp"
ApricornBoxTitleGFX:
INCBIN "gfx/items/apricorns/apricorn_box_title.2bpp"

ApricornBoxHeaderGFX:
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
	db %11111111
