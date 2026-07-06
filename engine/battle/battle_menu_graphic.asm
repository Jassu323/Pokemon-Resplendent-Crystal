DEF BATTLE_MENU_BUTTON_TILE_COUNT EQU 51
DEF BATTLE_MENU_BUTTON_WIDTH      EQU 10
DEF BATTLE_MENU_BUTTON_HEIGHT     EQU 3
DEF BATTLE_MENU_CURSOR_TILE       EQU $cc
DEF BATTLE_MENU_CURSOR_DEST_TILE  EQU BATTLE_MENU_CURSOR_TILE - $80

DEF BATTLE_MENU_ATTR_RED_YELLOW EQU $08 | PAL_BATTLE_BG_6
DEF BATTLE_MENU_ATTR_GREEN_BLUE EQU $08 | PAL_BATTLE_BG_TEXT

LoadBattleMenuGraphic::
	call BattleMenuGraphic_InitCursorPosition
	call BattleMenuGraphic_StageBlankRevealIfNeeded
	call BattleMenuGraphic_LoadGraphics
	call BattleMenuGraphic_LoadPalettes
	call BattleMenuGraphic_DrawButtons
	call BattleMenuGraphic_TransferTilemapAndAttrmap
	call BattleMenuGraphic_PlaceCursorOAM
	call BattleMenuGraphic_SetVisible

.loop
	call DelayFrame
	call JoyTextDelay
	call BattleMenuGraphic_HandleInput
	jr nc, .loop

	call BattleMenuGraphic_ClearCursorOAM
	ret

BattleMenuGraphic_TransferTilemapAndAttrmap:
	call HDMATransferTilemapAndAttrmap_Menu
	xor a
	ldh [hBGMapMode], a
	ret

BattleMenuGraphic_StageBlankRevealIfNeeded:
	ld hl, wBattleMenuGFXFlags
	bit BATTLE_MENU_GFX_STAGED_REVEAL_F, [hl]
	ret z
	res BATTLE_MENU_GFX_STAGED_REVEAL_F, [hl]
	call BattleMenuGraphic_TransferTilemapAndAttrmap
	ld b, SCGB_BATTLE_COLORS
	jp GetSGBLayout

BattleMenuGraphic_InitCursorPosition:
	ld a, [wBattleMenuCursorPosition]
	and a
	jr z, .reset
	cp 5
	ret c

.reset
	ld a, 1
	ld [wBattleMenuCursorPosition], a
	ret

BattleMenuGraphic_SetVisible:
	ld hl, wBattleMenuGFXFlags
	set BATTLE_MENU_GFX_VISIBLE_F, [hl]
	ret

BattleMenuGraphic_RestoreState::
	ld hl, wBattleMenuGFXFlags
	bit BATTLE_MENU_GFX_VISIBLE_F, [hl]
	ret z
	res BATTLE_MENU_GFX_VISIBLE_F, [hl]
	jp BattleMenuGraphic_RestorePalettes

BattleMenuGraphic_ClearForText::
	ld hl, wBattleMenuGFXFlags
	bit BATTLE_MENU_GFX_VISIBLE_F, [hl]
	ret z
	call BattleMenuGraphic_BlankLowerArea
	call HDMATransferTilemapAndAttrmap_Menu
	xor a
	ldh [hBGMapMode], a
	jp BattleMenuGraphic_RestoreState

BattleMenuGraphic_BlankLowerArea::
	hlcoord 0, 12
	lb bc, 6, SCREEN_WIDTH
	ld a, ' '
	call FillBoxWithByte

	hlcoord 0, 12, wAttrmap
	lb bc, 6, SCREEN_WIDTH
	ld a, PAL_BATTLE_BG_TEXT
	jp FillBoxWithByte

BattleMenuGraphic_LoadGraphics:
	call BattleMenuGraphic_LoadCursorGFX

	ld hl, wBattleMenuGFXFlags
	bit BATTLE_MENU_GFX_CLEAN_F, [hl]
	ret nz

	ld de, BattleMenuButtonsGFX
	ld hl, vTiles4
	lb bc, BANK(BattleMenuButtonsGFX), BATTLE_MENU_BUTTON_TILE_COUNT
	call Get2bppViaHDMAToVRAMBank1

	ld hl, wBattleMenuGFXFlags
	set BATTLE_MENU_GFX_CLEAN_F, [hl]
	ret

BattleMenuGraphic_LoadCursorGFX:
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld de, BattleMenuCursorGFX
	ld hl, vTiles1 tile BATTLE_MENU_CURSOR_DEST_TILE
	lb bc, BANK(BattleMenuCursorGFX), 1
	call Get2bppViaHDMA

	pop af
	ldh [rVBK], a
	ret

BattleMenuGraphic_LoadPalettes:
	ldh a, [hCGB]
	and a
	ret z

	ldh a, [rWBK]
	push af
	ld a, BANK(wGBCPalettes)
	ldh [rWBK], a

	ld hl, wBGPals1 palette PAL_BATTLE_BG_6
	ld de, wBattleMenuSavedBGPals
	ld bc, 2 palettes
	call CopyBytes

	ld hl, BattleMenuGraphicPalettes
	ld de, wBGPals1 palette PAL_BATTLE_BG_6
	ld bc, 2 palettes
	call CopyBytes

	ld hl, BattleMenuGraphicPalettes
	ld de, wBGPals2 palette PAL_BATTLE_BG_6
	ld bc, 2 palettes
	call CopyBytes

	pop af
	ldh [rWBK], a

	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

BattleMenuGraphic_RestorePalettes:
	ldh a, [hCGB]
	and a
	ret z

	ldh a, [rWBK]
	push af
	ld a, BANK(wGBCPalettes)
	ldh [rWBK], a

	ld hl, wBattleMenuSavedBGPals
	ld de, wBGPals1 palette PAL_BATTLE_BG_6
	ld bc, 2 palettes
	call CopyBytes

	ld hl, wBattleMenuSavedBGPals
	ld de, wBGPals2 palette PAL_BATTLE_BG_6
	ld bc, 2 palettes
	call CopyBytes

	pop af
	ldh [rWBK], a

	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

BattleMenuGraphic_DrawButtons:
	hlcoord 0, 12
	ld de, BattleMenuGraphicFightTilemap
	call BattleMenuGraphic_PlaceButtonTiles
	hlcoord 0, 12, wAttrmap
	ld a, BATTLE_MENU_ATTR_RED_YELLOW
	call BattleMenuGraphic_FillButtonAttrs

	hlcoord 10, 12
	ld de, BattleMenuGraphicPkmnTilemap
	call BattleMenuGraphic_PlaceButtonTiles
	hlcoord 10, 12, wAttrmap
	ld a, BATTLE_MENU_ATTR_GREEN_BLUE
	call BattleMenuGraphic_FillButtonAttrs

	hlcoord 0, 15
	ld de, BattleMenuGraphicPackTilemap
	call BattleMenuGraphic_PlaceButtonTiles
	hlcoord 0, 15, wAttrmap
	ld a, BATTLE_MENU_ATTR_RED_YELLOW
	call BattleMenuGraphic_FillButtonAttrs

	hlcoord 10, 15
	ld de, BattleMenuGraphicRunTilemap
	call BattleMenuGraphic_PlaceButtonTiles
	hlcoord 10, 15, wAttrmap
	ld a, BATTLE_MENU_ATTR_GREEN_BLUE
	jp BattleMenuGraphic_FillButtonAttrs

BattleMenuGraphic_PlaceButtonTiles:
	ld b, BATTLE_MENU_BUTTON_HEIGHT

.row
	push bc
	push hl
	ld c, BATTLE_MENU_BUTTON_WIDTH

.col
	ld a, [de]
	inc de
	ld [hli], a
	dec c
	jr nz, .col

	pop hl
	ld bc, SCREEN_WIDTH
	add hl, bc
	pop bc
	dec b
	jr nz, .row
	ret

BattleMenuGraphic_FillButtonAttrs:
	ld e, a
	ld b, BATTLE_MENU_BUTTON_HEIGHT

.row
	push bc
	push hl
	ld c, BATTLE_MENU_BUTTON_WIDTH

.col
	ld a, e
	ld [hli], a
	dec c
	jr nz, .col

	pop hl
	ld bc, SCREEN_WIDTH
	add hl, bc
	pop bc
	dec b
	jr nz, .row
	ret

BattleMenuGraphic_HandleInput:
	call GetMenuJoypad
	bit B_PAD_A, a
	jr nz, .select

	ld b, a
	ld a, [wBattleMenuCursorPosition]
	ld c, a

	bit B_PAD_RIGHT, b
	jr nz, .right
	bit B_PAD_LEFT, b
	jr nz, .left
	bit B_PAD_UP, b
	jr nz, .up
	bit B_PAD_DOWN, b
	jr nz, .down
	and a
	ret

.right
	ld a, c
	bit 0, a
	jr z, .no_move
	inc a
	jr .move

.left
	ld a, c
	bit 0, a
	jr nz, .no_move
	dec a
	jr .move

.up
	ld a, c
	cp 3
	jr c, .no_move
	sub 2
	jr .move

.down
	ld a, c
	cp 3
	jr nc, .no_move
	add 2

.move
	ld [wBattleMenuCursorPosition], a
	call BattleMenuGraphic_PlaceCursorOAM

.no_move
	and a
	ret

.select
	ld a, PAD_A
	call MenuClickSound
	scf
	ret

BattleMenuGraphic_PlaceCursorOAM:
	ld a, [wBattleMenuCursorPosition]
	dec a
	add a
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, BattleMenuGraphicCursorCoords
	add hl, de
	ld de, wShadowOAMSprite14
	ld bc, BattleMenuGraphicCursorAttrs
	ld a, 4

.loop
	push af
	ld a, [hli]
	add 16
	ld [de], a
	inc de
	ld a, [hli]
	add 8
	ld [de], a
	inc de
	ld a, BATTLE_MENU_CURSOR_TILE
	ld [de], a
	inc de
	ld a, [bc]
	inc bc
	ld [de], a
	inc de
	pop af
	dec a
	jr nz, .loop
	ret

BattleMenuGraphic_ClearCursorOAM:
	ld hl, wShadowOAMSprite14YCoord
	ld de, OBJ_SIZE
	ld b, 4
	ld a, OAM_YCOORD_HIDDEN

.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	ret

BattleMenuGraphicPalettes:
	RGB 31, 31, 31
	RGB 31, 25,  0
	RGB 31,  0,  0
	RGB  0,  0,  0

	RGB 31, 31, 31
	RGB  0, 23,  0
	RGB  0, 13, 31
	RGB  0,  0,  0

BattleMenuGraphicFightTilemap:
	db $80, $81, $82, $83, $81, $84, $81, $81, $81, $85
	db $86, $87, $88, $89, $8a, $8b, $8c, $8d, $87, $8e
	db $8f, $90, $90, $91, $92, $93, $90, $90, $90, $94

BattleMenuGraphicPkmnTilemap:
	db $95, $96, $97, $98, $99, $96, $96, $96, $96, $9a
	db $9b, $9c, $9d, $9e, $9f, $a0, $a1, $a2, $9c, $a3
	db $a4, $a5, $a5, $a5, $a5, $a5, $a5, $a5, $a5, $a6

BattleMenuGraphicPackTilemap:
	db $95, $96, $97, $98, $96, $96, $a7, $96, $96, $9a
	db $9b, $9c, $9d, $a8, $a9, $aa, $ab, $ac, $9c, $a3
	db $a4, $a5, $a5, $a5, $a5, $a5, $a5, $a5, $a5, $a6

BattleMenuGraphicRunTilemap:
	db $80, $81, $81, $ad, $ae, $81, $81, $81, $81, $85
	db $86, $87, $87, $af, $b0, $b1, $b2, $87, $87, $8e
	db $8f, $90, $90, $90, $90, $90, $90, $90, $90, $94

BattleMenuGraphicCursorCoords:
	db  97,   1,  97,  71, 111,   1, 111,  71
	db  97,  81,  97, 151, 111,  81, 111, 151
	db 121,   1, 121,  71, 135,   1, 135,  71
	db 121,  81, 121, 151, 135,  81, 135, 151

BattleMenuGraphicCursorAttrs:
	db PAL_BATTLE_OB_GRAY
	db PAL_BATTLE_OB_GRAY | OAM_XFLIP
	db PAL_BATTLE_OB_GRAY | OAM_YFLIP
	db PAL_BATTLE_OB_GRAY | OAM_XFLIP | OAM_YFLIP
