; Pack.Jumptable and BattlePack.Jumptable indexes
	const_def
	const PACKSTATE_INITGFX            ;  0
	const PACKSTATE_INITITEMSPOCKET    ;  1
	const PACKSTATE_ITEMSPOCKETMENU    ;  2
	const PACKSTATE_INITBALLSPOCKET    ;  3
	const PACKSTATE_BALLSPOCKETMENU    ;  4
	const PACKSTATE_INITKEYITEMSPOCKET ;  5
	const PACKSTATE_KEYITEMSPOCKETMENU ;  6
	const PACKSTATE_INITBERRIESPOCKET  ;  7
	const PACKSTATE_BERRIESPOCKETMENU  ;  8
	const PACKSTATE_INITMEDICINEPOCKET ;  9
	const PACKSTATE_MEDICINEPOCKETMENU ; 10
	const PACKSTATE_QUITNOSCRIPT       ; 11
	const PACKSTATE_QUITRUNSCRIPT      ; 12

DEF PACK_POCKET_NAME_UPPER_LEFT_TILE EQU $00
DEF PACK_POCKET_NAME_UPPER_MIDDLE_TILE EQU PACK_POCKET_NAME_UPPER_LEFT_TILE + 1
DEF PACK_POCKET_NAME_UPPER_RIGHT_TILE EQU PACK_POCKET_NAME_UPPER_MIDDLE_TILE + 1
DEF PACK_POCKET_NAME_TILE EQU PACK_POCKET_NAME_UPPER_RIGHT_TILE + 1
DEF PACK_POCKET_NAME_BOTTOM_LEFT_TILE EQU PACK_POCKET_NAME_TILE + 5
DEF PACK_POCKET_NAME_BOTTOM_MIDDLE_TILE EQU PACK_POCKET_NAME_BOTTOM_LEFT_TILE + 1
DEF PACK_POCKET_NAME_BOTTOM_RIGHT_TILE EQU PACK_POCKET_NAME_BOTTOM_MIDDLE_TILE + 1
DEF PACK_BORDER_TILE EQU PACK_POCKET_NAME_BOTTOM_RIGHT_TILE + 1
DEF PACK_POCKET_SWITCH_TILE EQU PACK_BORDER_TILE + 1
DEF PACK_POCKET_SORT_TILE EQU PACK_POCKET_SWITCH_TILE + 6
DEF PACK_GFX_TILE EQU PACK_POCKET_SORT_TILE + 6
DEF PACK_GFX_TILES EQU 15
DEF PACK_TITLE_TILE EQU PACK_GFX_TILE + PACK_GFX_TILES
DEF PACK_TITLE_TILES EQU 6
DEF PACK_HEADER_TILE EQU PACK_TITLE_TILE + PACK_TITLE_TILES
DEF PACK_BLANK_TILE EQU $7f
DEF PACK_VISIBLE_ITEMS EQU 8
DEF PACK_ROW_LENGTH EQU 4
DEF PACK_ICON_ROW_BUFFERS EQU 4
DEF PACK_ITEM_ICON_TILES EQU 9
DEF PACK_ITEM_ICON_SIGNED_FIRST_TILE EQU $80
DEF PACK_ITEM_ICON_SIGNED_DEST_TILE EQU PACK_ITEM_ICON_SIGNED_FIRST_TILE - $80
DEF PACK_ITEM_ICON_OAM_FIRST_TILE EQU PACK_ITEM_ICON_SIGNED_FIRST_TILE + PACK_ROW_LENGTH * PACK_ITEM_ICON_TILES
DEF PACK_ITEM_ICON_OAM_DEST_TILE EQU PACK_ITEM_ICON_OAM_FIRST_TILE - $80
DEF PACK_ITEM_ICON_OAM_SECOND_FIRST_TILE EQU PACK_ITEM_ICON_OAM_FIRST_TILE + PACK_ITEM_ICON_TILES
DEF PACK_ITEM_ICON_OAM_SECOND_DEST_TILE EQU PACK_ITEM_ICON_OAM_DEST_TILE + PACK_ITEM_ICON_TILES
DEF PACK_ITEM_ICON_OAM_THIRD_FIRST_TILE EQU PACK_ITEM_ICON_OAM_SECOND_FIRST_TILE + PACK_ITEM_ICON_TILES
DEF PACK_ITEM_ICON_OAM_THIRD_DEST_TILE EQU PACK_ITEM_ICON_OAM_SECOND_DEST_TILE + PACK_ITEM_ICON_TILES
DEF PACK_ITEM_ICON_FIRST_TILE EQU $70
DEF PACK_ITEM_ICON_FIRST_PALETTE EQU 1
DEF PACK_ITEM_ICON_PALETTES EQU 7
DEF PACK_ITEM_ICON_RECORD_SIZE EQU 3
DEF PACK_ITEM_ICON_OAM_FIRST_PALETTE EQU 1
DEF PACK_ITEM_ICON_OAM_SECOND_PALETTE EQU PACK_ITEM_ICON_OAM_FIRST_PALETTE + 1
DEF PACK_ITEM_ICON_OAM_THIRD_PALETTE EQU PACK_ITEM_ICON_OAM_SECOND_PALETTE + 1
DEF PACK_ITEM_ICON_OVERFLOW_SLOT_PAGE_UP EQU 0
DEF PACK_ITEM_ICON_OVERFLOW_SLOT_PAGE_DOWN EQU PACK_ROW_LENGTH
DEF PACK_ITEM_ICON_NO_OVERFLOW EQU $ff

Pack:
	ld hl, wOptions
	set NO_TEXT_SCROLL, [hl]
	ld a, $1
	ldh [hInMenu], a
	call InitPackBuffers
.loop
	call JoyTextDelay
	ld a, [wJumptableIndex]
	bit JUMPTABLE_EXIT_F, a
	jr nz, .done
	call .RunJumptable
	call DelayFrame
	jr .loop

.done
	ld a, [wCurPocket]
	ld [wLastPocket], a
	ld hl, wOptions
	res NO_TEXT_SCROLL, [hl]
	xor a
	ldh [hInMenu], a
	ret

.RunJumptable:
	ld a, [wJumptableIndex]
	ld hl, .Jumptable
	call Pack_GetJumptablePointer
	jp hl

.Jumptable:
; entries correspond to PACKSTATE_* constants
	dw .InitGFX            ;  0
	dw .InitItemsPocket    ;  1
	dw .ItemsPocketMenu    ;  2
	dw .InitBallsPocket    ;  3
	dw .BallsPocketMenu    ;  4
	dw .InitKeyItemsPocket ;  5
	dw .KeyItemsPocketMenu ;  6
	dw .InitBerriesPocket  ;  7
	dw .BerriesPocketMenu  ;  8
	dw .InitMedicinePocket ;  9
	dw .MedicinePocketMenu ; 10
	dw Pack_QuitNoScript   ; 11
	dw Pack_QuitRunScript  ; 12

.InitGFX:
	xor a
	ldh [hBGMapMode], a
	call Pack_InitGFX
	call Pack_PlaceCursor
	ld a, [wPackJumptableIndex]
	inc a
	ld [wJumptableIndex], a
	ret

.InitItemsPocket:
	xor a ; ITEM_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

.ItemsPocketMenu:
	ld b, PACKSTATE_INITMEDICINEPOCKET ; left
	ld c, PACKSTATE_INITBALLSPOCKET ; right
	jp Pack_ShellPocketMenu

.InitKeyItemsPocket:
	ld a, KEY_ITEM_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

.KeyItemsPocketMenu:
	ld b, PACKSTATE_INITBALLSPOCKET ; left
	ld c, PACKSTATE_INITBERRIESPOCKET ; right
	jp Pack_ShellPocketMenu

.InitBerriesPocket:
	ld a, BERRY_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

.BerriesPocketMenu:
	ld b, PACKSTATE_INITKEYITEMSPOCKET ; left
	ld c, PACKSTATE_INITMEDICINEPOCKET ; right
	jp Pack_ShellPocketMenu

.InitBallsPocket:
	ld a, BALL_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

.BallsPocketMenu:
	ld b, PACKSTATE_INITITEMSPOCKET ; left
	ld c, PACKSTATE_INITKEYITEMSPOCKET ; right
	jp Pack_ShellPocketMenu

.InitMedicinePocket:
	ld a, MEDICINE_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

.MedicinePocketMenu:
	ld b, PACKSTATE_INITBERRIESPOCKET ; left
	ld c, PACKSTATE_INITITEMSPOCKET ; right
	jp Pack_ShellPocketMenu

Pack_InitPocketShell:
	call Pack_RedrawCurrentPocketShell
	jp Pack_JumptableNext

Pack_RedrawCurrentPocketShell:
	call Pack_LoadCurrentPocketNameGFX
	call Pack_DrawShellNoCursor_BlankIcons
	call DrawPackGFX
	call Pack_HideOverflowItemIconOAM
	call Pack_TransferTilemapAndAttrmap
	call Pack_DrawVisibleItemIconsDeferredOAM
	call Pack_ApplyVisibleItemIconPalettes
	call Pack_PrintSelectedItemText
	call Pack_TransferTilemapAndAttrmap
	call Pack_ShowOverflowItemIconOAM
	call Pack_PlaceCursor
	call Pack_LoadAdjacentItemIconRows
	ret

Pack_ShellPocketMenu:
	push bc
	call Pack_PlaceCursor
	pop bc
	ldh a, [hJoyPressed]
	bit B_PAD_B, a
	jr nz, .b_button
	bit B_PAD_A, a
	jr nz, .a_button
	bit B_PAD_SELECT, a
	jr nz, .select_button
	bit B_PAD_START, a
	jr nz, .start_button
	ldh a, [hJoyLast]
	bit B_PAD_LEFT, a
	jp nz, .d_left
	bit B_PAD_RIGHT, a
	jp nz, .d_right
	bit B_PAD_UP, a
	jp nz, .d_up
	bit B_PAD_DOWN, a
	jp nz, .d_down
	ret

	.b_button
	ld a, PAD_B
	call MenuClickSound
	ld a, [wSwitchItem]
	and a
	jr nz, .cancel_switch_item
	call Pack_HideCursor
	ld a, PACKSTATE_QUITNOSCRIPT
	ld [wJumptableIndex], a
	ret

	.a_button
	call Pack_SelectCurrentItem
	ret nc
	ld a, PAD_A
	call MenuClickSound
	ld a, [wSwitchItem]
	and a
	jr nz, .place_switch_item
	call Pack_HideCursor
	ld a, [wBattleMode]
	and a
	jr nz, .battle_item_submenu
	call Pack_LoadItemSubmenu
	jr .return_from_item_submenu

.battle_item_submenu
	call ItemSubmenu

.return_from_item_submenu
	ld a, [wJumptableIndex]
	cp PACKSTATE_QUITNOSCRIPT
	ret z
	cp PACKSTATE_QUITRUNSCRIPT
	ret z
	xor a
	ldh [hBGMapMode], a
	call Pack_InitGFX
	jp Pack_PlaceCursor

	.select_button
	call Pack_SelectCurrentItem
	ret nc
	ld a, [wSwitchItem]
	and a
	jr nz, .place_switch_item
	call Pack_StartSwitchItem
	ret

	.place_switch_item
	call Pack_PlaceSwitchItem
	ret

	.cancel_switch_item
	call Pack_ClearSwitchItemCursor
	xor a
	ld [wSwitchItem], a
	jp Pack_UpdateSelectedItemText

	.start_button
	ld a, [wSwitchItem]
	and a
	ret nz
	ld a, PAD_START
	call MenuClickSound
	call Pack_GetCurrentPocketItemCount
	cp 2
	jr c, .not_enough_items_to_sort
	ld hl, SortItemsText
	call Pack_MenuTextbox
	call Pack_YesNoBox
	push af
	call Pack_CloseWindow
	pop af
	jr c, .cancel_sort
	farcall SortItemsInBag
	jr nc, .cancel_sort
	call Pack_ResetSortedPocketPosition
	ld de, SFX_SWITCH_POKEMON
	call WaitPlaySFX
	ld de, SFX_SWITCH_POKEMON
	call WaitPlaySFX
	jp Pack_RedrawCurrentPocketAfterSort

.not_enough_items_to_sort
	ld hl, NotEnoughItemsToSortText
	call Pack_PrintTextNoScroll

.cancel_sort
	jp Pack_UpdateSelectedItemText

.d_left
	push bc
	call Pack_MoveCursorLeft
	pop bc
	jr nc, .place_cursor
	ld a, [wSwitchItem]
	and a
	jr nz, .place_cursor
	ld a, b
	jr .switch_pocket

	.d_right
	push bc
	call Pack_MoveCursorRight
	pop bc
	jr nc, .place_cursor
	ld a, [wSwitchItem]
	and a
	jr nz, .place_cursor
	ld a, c

	.switch_pocket
	push af
	call Pack_HideCursor
	pop af
	ld [wJumptableIndex], a
	ld [wPackJumptableIndex], a
	ld de, SFX_SWITCH_POCKETS
	call PlaySFX
	ret

	.place_cursor
	call Pack_PlaceCursor
	ld a, [wSwitchItem]
	and a
	jr z, .update_selected_item_text
	call Pack_PrintSelectedItemText
	jp Pack_PrintMoveItemPrompt

	.update_selected_item_text
	jp Pack_UpdateSelectedItemText

.d_up
	call Pack_ClearSwitchItemCursor
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	push af
	call Pack_MoveCursorUp
	call Pack_GetPocketScrollPointer
	ld b, [hl]
	pop af
	cp b
	jr z, .place_cursor
	call Pack_RedrawVisibleItemIconsPageUp
	call Pack_PlaceCursor
	call Pack_LoadPreviousCachedItemIconRow
	call Pack_LoadAdjacentItemIconOAMCaches
	jp Pack_PrintMoveItemPromptIfSwitching

.d_down
	call Pack_ClearSwitchItemCursor
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	push af
	call Pack_MoveCursorDown
	call Pack_GetPocketScrollPointer
	ld b, [hl]
	pop af
	cp b
	jr z, .place_cursor
	call Pack_RedrawVisibleItemIconsPageDown
	call Pack_PlaceCursor
	call Pack_LoadNextCachedItemIconRow
	call Pack_LoadAdjacentItemIconOAMCaches
	jp Pack_PrintMoveItemPromptIfSwitching

Pack_MoveCursorLeft:
	call Pack_NormalizeCursorPosition
	call Pack_GetPocketCursorPointer
	ld a, [hl]
	and a
	jr z, .switch_pocket
	dec a
	and PACK_ROW_LENGTH - 1
	jr z, .switch_pocket
	ld a, [hl]
	dec a
	call Pack_SetCursorIfSlotValid
	and a
	ret

.switch_pocket
	scf
	ret

Pack_MoveCursorRight:
	call Pack_NormalizeCursorPosition
	call Pack_GetPocketCursorPointer
	ld a, [hl]
	and a
	jr z, .switch_pocket
	ld b, a
	dec a
	and PACK_ROW_LENGTH - 1
	cp PACK_ROW_LENGTH - 1
	jr z, .switch_pocket
	ld a, b
	inc a
	push af
	call Pack_IsCursorSlotValid
	jr nc, .invalid
	pop af
	push af
	call Pack_GetPocketCursorPointer
	pop af
	ld [hl], a
	and a
	ret

.invalid
	pop af

.switch_pocket
	scf
	ret

Pack_MoveCursorUp:
	call Pack_NormalizeCursorPosition
	call Pack_GetPocketCursorPointer
	ld a, [hl]
	and a
	ret z
	cp PACK_ROW_LENGTH + 1
	jr c, .previous_page
	sub PACK_ROW_LENGTH
	ld [hl], a
	ret

.previous_page
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	and a
	ret z
	sub PACK_ROW_LENGTH
	ld [hl], a
	ret

Pack_MoveCursorDown:
	call Pack_NormalizeCursorPosition
	call Pack_GetPocketCursorPointer
	ld a, [hl]
	and a
	ret z
	cp PACK_ROW_LENGTH + 1
	jr nc, .next_page
	add PACK_ROW_LENGTH
	call Pack_SetCursorIfSlotValid
	and a
	ret

.next_page
	call Pack_GetCurrentPocketItemCount
	ld c, a
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	add PACK_VISIBLE_ITEMS
	cp c
	ret nc

	ld a, [hl]
	add PACK_ROW_LENGTH
	ld [hl], a
	jp Pack_NormalizeCursorPosition

Pack_SetCursorIfSlotValid:
	push af
	call Pack_IsCursorSlotValid
	jr nc, .invalid
	pop af
	push af
	call Pack_GetPocketCursorPointer
	pop af
	ld [hl], a
	and a
	ret

.invalid
	pop af
	and a
	ret

Pack_IsCursorSlotValid:
	and a
	ret z
	ld b, a
	call Pack_GetCurrentPocketItemCount
	ld c, a
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	add b
	cp c
	jr c, .valid
	jr z, .valid
	and a
	ret

.valid
	scf
	ret

Pack_NormalizeCursorPosition:
	call Pack_GetCurrentPocketItemCount
	ld b, a
	and a
	jr nz, .has_items
	call Pack_GetPocketCursorPointer
	xor a
	ld [hl], a
	call Pack_GetPocketScrollPointer
	xor a
	ld [hl], a
	jp Pack_HideCursor

.has_items
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	and $fc
	ld [hl], a
	cp b
	jr c, .scroll_ok
	xor a
	ld [hl], a

.scroll_ok
	ld a, b
	sub [hl]
	ld e, a
	cp PACK_VISIBLE_ITEMS
	jr c, .got_visible_count
	ld e, PACK_VISIBLE_ITEMS

.got_visible_count
	ld a, e
	push af
	call Pack_GetPocketCursorPointer
	pop af
	ld e, a
	ld a, [hl]
	and a
	jr z, .set_first_slot
	cp e
	ret c
	ret z
	ld [hl], e
	ret

.set_first_slot
	ld [hl], 1
	ret

Pack_PlaceCursor:
	call Pack_NormalizeCursorPosition
	call Pack_GetPocketCursorPointer
	ld a, [hl]
	and a
	jr z, Pack_HideCursor
	dec a
	ld hl, PackCursorPositions
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

Pack_HideCursor:
	xor a
	ld [wShadowOAMSprite00YCoord], a
	ret

Pack_GetPocketCursorPointer:
	call Pack_GetPocketPositionOffset
	ld hl, wItemsPocketCursor
	add hl, de
	ret

Pack_GetPocketScrollPointer:
	call Pack_GetPocketPositionOffset
	ld hl, wItemsPocketScrollPosition
	add hl, de
	ret

Pack_GetPocketPositionOffset:
	ld a, [wCurPocket]
	cp NUM_POCKETS
	jr c, .valid_pocket
	xor a

.valid_pocket
	ld e, a
	ld d, 0
	ld hl, .cursor_order
	add hl, de
	ld e, [hl]
	ld d, 0
	ret

.cursor_order
	db 0 ; ITEM_POCKET
	db 2 ; BALL_POCKET
	db 1 ; KEY_ITEM_POCKET
	db 3 ; BERRY_POCKET
	db 4 ; MEDICINE_POCKET

Pack_GetCurrentPocketItemCount:
	ld a, [wCurPocket]
	cp NUM_POCKETS
	jr c, .valid_pocket
	xor a

	.valid_pocket
	ld e, a
	ld d, 0
	ld a, [wBattleType]
	cp BATTLETYPE_TUTORIAL
	ld hl, .counts
	jr nz, .got_counts
	ld hl, .tutorial_counts

.got_counts
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [hl]
	ret

.counts
	dw wNumItems
	dw wNumBalls
	dw wNumKeyItems
	dw wNumBerries
	dw wNumMedicine

.tutorial_counts
	dw wDudeNumItems
	dw wDudeNumBalls
	dw wDudeNumKeyItems
	dw wDudeNumBerries
	dw wDudeNumMedicine

Pack_GetCurrentPocketListPointer:
	ld a, [wCurPocket]
	cp NUM_POCKETS
	jr c, .valid_pocket
	xor a

.valid_pocket
	ld e, a
	ld d, 0
	ld h, d
	ld l, e
	add hl, hl
	add hl, de
	ld a, [wBattleType]
	cp BATTLETYPE_TUTORIAL
	ld de, .pockets
	jr nz, .got_pockets
	ld de, .tutorial_pockets

.got_pockets
	add hl, de
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld c, [hl]
	ld h, d
	ld l, e
	ret

.pockets
	dw wNumItems
	db 2
	dw wNumBalls
	db 2
	dw wNumKeyItems
	db 1
	dw wNumBerries
	db 2
	dw wNumMedicine
	db 2

.tutorial_pockets
	dw wDudeNumItems
	db 2
	dw wDudeNumBalls
	db 2
	dw wDudeNumKeyItems
	db 1
	dw wDudeNumBerries
	db 2
	dw wDudeNumMedicine
	db 2

Pack_GetVisibleSlotItem:
	call Pack_GetVisibleSlotItemEntry
	ret nc
	ld a, [hl]
	scf
	ret

Pack_GetVisibleSlotItemEntry:
	ld b, a
	call Pack_GetCurrentPocketItemCount
	ld c, a
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	add b
	jr Pack_GetAbsoluteSlotItemEntry_WithCount

Pack_GetAbsoluteSlotItem:
	call Pack_GetAbsoluteSlotItemEntry
	ret nc
	ld a, [hl]
	scf
	ret

Pack_GetAbsoluteSlotItemEntry:
	ld b, a
	call Pack_GetCurrentPocketItemCount
	ld c, a
	ld a, b

Pack_GetAbsoluteSlotItemEntry_WithCount:
	cp c
	jr nc, .none
	push af
	call Pack_GetCurrentPocketListPointer
	inc hl
	pop af
	and a
	jr z, .got_item
	ld b, a

.item_loop
	ld a, c
	add l
	ld l, a
	jr nc, .no_carry
	inc h

.no_carry
	dec b
	jr nz, .item_loop

.got_item
	scf
	ret

.none
	and a
	ret

Pack_SelectCurrentItem:
	call Pack_GetPocketCursorPointer
	ld a, [hl]
	and a
	jr z, .none
	dec a
	call Pack_GetVisibleSlotItemEntry
	jr nc, .none
	ld a, [hl]
	ld [wMenuSelection], a
	ld [wCurItem], a
	ld a, c
	cp 1
	jr z, .key_item
	inc hl
	ld a, [hl]
	jr .got_quantity

.key_item
	ld a, 1

.got_quantity
	ld [wMenuSelectionQuantity], a
	ld [wItemQuantity], a
	ld [wCurItemQuantity], a
	scf
	ret

.none
	and a
	ret

Pack_StartSwitchItem:
	call Pack_SetupSwitchItemContext
	ret nc
	farcall SwitchItemsInBag
	call Pack_PrintSelectedItemText
	jp Pack_PrintMoveItemPrompt

Pack_PlaceSwitchItem:
	call Pack_SetupSwitchItemContext
	ret nc
	call Pack_ClearSwitchItemCursor
	farcall SwitchItemsInBag
	ld de, SFX_SWITCH_POKEMON
	call WaitPlaySFX
	ld de, SFX_SWITCH_POKEMON
	call WaitPlaySFX
	jp Pack_RedrawCurrentPocketAfterSort

Pack_PrintMoveItemPrompt:
	call Pack_PlaceSwitchItemCursor
	ld hl, AskItemMoveText
	jp Pack_PrintTextNoScroll

Pack_PrintMoveItemPromptIfSwitching:
	ld a, [wSwitchItem]
	and a
	ret z
	jp Pack_PrintMoveItemPrompt

Pack_PlaceSwitchItemCursor:
	call Pack_GetVisibleSwitchItemSlot
	ret nc
	ld d, '▷'
	jr Pack_SetSwitchItemCursor

Pack_ClearSwitchItemCursor:
	call Pack_GetVisibleSwitchItemSlot
	ret nc
	ld d, ' '
	; fallthrough

Pack_SetSwitchItemCursor:
	call Pack_GetSwitchItemCursorCoord
	push bc
	call Coord2Tile
	ld [hl], d
	pop bc
	call Coord2Attr
	xor a
	ld [hl], a
	ret

Pack_GetVisibleSwitchItemSlot:
	ld a, [wSwitchItem]
	and a
	jr z, .not_visible
	dec a
	ld b, a
	call Pack_GetPocketScrollPointer
	ld a, b
	cp [hl]
	jr c, .not_visible
	sub [hl]
	cp PACK_VISIBLE_ITEMS
	jr nc, .not_visible
	scf
	ret

.not_visible
	and a
	ret

Pack_GetSwitchItemCursorCoord:
	ld hl, PackCursorTileCoords
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld c, [hl]
	inc hl
	ld b, [hl]
	ret

Pack_SetupSwitchItemContext:
	call Pack_GetPocketCursorPointer
	ld a, [hl]
	and a
	jr z, .none
	ld b, a
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	add b
	dec a
	ld [wScrollingMenuCursorPosition], a
	call Pack_GetCurrentPocketListPointer
	ld a, l
	ld [wMenuData_ItemsPointerAddr], a
	ld a, h
	ld [wMenuData_ItemsPointerAddr + 1], a
	ld a, c
	ld [wMenuData_ScrollingMenuItemFormat], a
	scf
	ret

.none
	and a
	ret

Pack_LoadItemSubmenu:
	farcall _CheckTossableItem
	ld a, [wItemAttributeValue]
	and a
	jr nz, .tossable
	farcall CheckSelectableItem
	ld a, [wItemAttributeValue]
	and a
	jr nz, .selectable
	farcall CheckItemMenu
	ld a, [wItemAttributeValue]
	and a
	jr nz, .usable
	jr .unusable

.selectable
	farcall CheckItemMenu
	ld a, [wItemAttributeValue]
	and a
	jr nz, .selectable_usable
	jr .selectable_unusable

.tossable
	farcall CheckSelectableItem
	ld a, [wItemAttributeValue]
	and a
	jr nz, .tossable_selectable
	jr .tossable_unselectable

.usable
	ld hl, MenuHeader_UsableKeyItem
	ld de, Jumptable_UseGiveTossRegisterQuit
	jr .build_menu

.selectable_usable
	ld hl, MenuHeader_UsableItem
	ld de, Jumptable_UseGiveTossQuit
	jr .build_menu

.tossable_selectable
	ld hl, MenuHeader_UnusableItem
	ld de, Jumptable_UseQuit
	jr .build_menu

.tossable_unselectable
	ld hl, MenuHeader_UnusableKeyItem
	ld de, Jumptable_UseRegisterQuit
	jr .build_menu

.unusable
	ld hl, MenuHeader_HoldableKeyItem
	ld de, Jumptable_GiveTossRegisterQuit
	jr .build_menu

.selectable_unusable
	ld hl, MenuHeader_HoldableItem
	ld de, Jumptable_GiveTossQuit
	.build_menu
	push hl
	push de
	pop de
	pop hl
	push de
	call LoadMenuHeader
	call Pack_VerticalMenu
	call Pack_CloseWindow
	pop hl
	ret c
	ld a, [wMenuCursorY]
	dec a
	call Pack_GetJumptablePointer
	jp hl

Pack_PrepareItemSubmenuAttrs:
	call MenuBoxCoord2Attr
	call GetMenuBoxDims
	inc b
	inc c
	xor a
	jp FillBoxWithByte

MenuHeader_UsableKeyItem:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 5 ; items
	db "USE@"
	db "GIVE@"
	db "TOSS@"
	db "SEL@"
	db "QUIT@"

Jumptable_UseGiveTossRegisterQuit:
	dw UseItem
	dw GiveItem
	dw TossMenu
	dw RegisterItem
	dw QuitItemSubmenu

MenuHeader_UsableItem:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 3, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 4 ; items
	db "USE@"
	db "GIVE@"
	db "TOSS@"
	db "QUIT@"

Jumptable_UseGiveTossQuit:
	dw UseItem
	dw GiveItem
	dw TossMenu
	dw QuitItemSubmenu

MenuHeader_UnusableItem:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 7, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 2 ; items
	db "USE@"
	db "QUIT@"

Jumptable_UseQuit:
	dw UseItem
	dw QuitItemSubmenu

MenuHeader_UnusableKeyItem:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 5, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 3 ; items
	db "USE@"
	db "SEL@"
	db "QUIT@"

Jumptable_UseRegisterQuit:
	dw UseItem
	dw RegisterItem
	dw QuitItemSubmenu

MenuHeader_HoldableKeyItem:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 3, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 4 ; items
	db "GIVE@"
	db "TOSS@"
	db "SEL@"
	db "QUIT@"

Jumptable_GiveTossRegisterQuit:
	dw GiveItem
	dw TossMenu
	dw RegisterItem
	dw QuitItemSubmenu

MenuHeader_HoldableItem:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 5, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 3 ; items
	db "GIVE@"
	db "TOSS@"
	db "QUIT@"

Jumptable_GiveTossQuit:
	dw GiveItem
	dw TossMenu
	dw QuitItemSubmenu

UseItem:
	farcall CheckItemMenu
	ld a, [wItemAttributeValue]
	ld hl, .dw
	rst JumpTable
	ret

.dw
; entries correspond to ITEMMENU_* constants
	dw .Oak     ; ITEMMENU_NOUSE
	dw .Oak
	dw .Oak
	dw .Oak
	dw .Current ; ITEMMENU_CURRENT
	dw .Party   ; ITEMMENU_PARTY
	dw .Field   ; ITEMMENU_CLOSE

.Oak:
	ld hl, OakThisIsntTheTimeText
	call Pack_PrintTextNoScroll
	ret

.Current:
	call DoItemEffect
	ret

.Party:
	ld a, [wPartyCount]
	and a
	jr z, .NoPokemon
	call DoItemEffect
	xor a
	ldh [hBGMapMode], a
	call Pack_InitGFX
	ret

.NoPokemon:
	ld hl, YouDontHaveAMonText
	call Pack_PrintTextNoScroll
	ret

.Field:
	call DoItemEffect
	ld a, [wItemEffectSucceeded]
	and a
	jr z, .Oak
	ld a, PACKSTATE_QUITRUNSCRIPT
	ld [wJumptableIndex], a
	ret

TossMenu:
	ld hl, AskThrowAwayText
	call Pack_PrintTextNoScroll
	call Pack_SelectQuantityToToss
	push af
	call Pack_CloseWindow
	pop af
	jr c, .finish
	call Pack_GetItemName
	ld hl, AskQuantityThrowAwayText
	call Pack_MenuTextbox
	call Pack_YesNoBox
	push af
	call Pack_CloseWindow
	pop af
	jr c, .finish
	ld hl, wNumItems
	ld a, [wCurItemQuantity]
	call TossItem
	call Pack_GetItemName
	ld hl, ThrewAwayText
	call Pack_PrintTextNoScroll
.finish
	ret

ResetPocketCursorPositions: ; unreferenced
	ld a, [wCurPocket]
	assert ITEM_POCKET == 0
	and a
	jr z, .items
	assert BALL_POCKET == 1
	dec a
	jr z, .balls
	assert KEY_ITEM_POCKET == 2
	dec a
	jr z, .key
	assert BERRY_POCKET == 3
	dec a
	jr z, .berries
	assert MEDICINE_POCKET == 4
	dec a
	jr z, .medicine
	ret

.balls
	xor a
	ld [wBallsPocketCursor], a
	ld [wBallsPocketScrollPosition], a
	ret

.items
	xor a
	ld [wItemsPocketCursor], a
	ld [wItemsPocketScrollPosition], a
	ret

.key
	xor a
	ld [wKeyItemsPocketCursor], a
	ld [wKeyItemsPocketScrollPosition], a
	ret

.berries
	xor a
	ld [wBerriesPocketCursor], a
	ld [wBerriesPocketScrollPosition], a
	ret

.medicine
	xor a
	ld [wMedicinePocketCursor], a
	ld [wMedicinePocketScrollPosition], a
	ret

RegisterItem:
	farcall CheckSelectableItem
	ld a, [wItemAttributeValue]
	and a
	jr nz, .cant_register
	ld a, [wCurPocket]
	rrca
	rrca
	and REGISTERED_POCKET
	ld b, a
	ld a, [wCurItemQuantity]
	inc a
	and REGISTERED_NUMBER
	or b
	ld [wWhichRegisteredItem], a
	ld a, [wCurItem]
	ld [wRegisteredItem], a
	call Pack_GetItemName
	ld de, SFX_FULL_HEAL
	call WaitPlaySFX
	ld hl, RegisteredItemText
	call Pack_PrintTextNoScroll
	ret

.cant_register
	ld hl, CantRegisterText
	call Pack_PrintTextNoScroll
	ret

GiveItem:
	ld a, [wPartyCount]
	and a
	jp z, .NoPokemon
	ld a, [wOptions]
	push af
	res NO_TEXT_SCROLL, a
	ld [wOptions], a
	ld a, PARTYMENUACTION_GIVE_ITEM
	ld [wPartyMenuActionText], a
	call ClearBGPalettes
	farcall LoadPartyMenuGFX
	farcall InitPartyMenuWithCancel
	farcall InitPartyMenuGFX
.loop
	farcall WritePartyMenuTilemap
	farcall PlacePartyMenuText
	call WaitBGMap
	call SetDefaultBGPAndOBP
	call DelayFrame
	farcall PartyMenuSelect
	jr c, .finish
	ld a, [wCurPartySpecies]
	cp EGG
	jr nz, .give
	ld hl, .AnEggCantHoldAnItemText
	call PrintText
	jr .loop

.give
	ld a, [wJumptableIndex]
	push af
	ld a, [wPackJumptableIndex]
	push af
	call GetCurNickname
	ld hl, wStringBuffer1
	ld de, wMonOrItemNameBuffer
	ld bc, MON_NAME_LENGTH
	call CopyBytes
	farcall TryGiveItemToPartymon
	pop af
	ld [wPackJumptableIndex], a
	pop af
	ld [wJumptableIndex], a
.finish
	pop af
	ld [wOptions], a
	xor a
	ldh [hBGMapMode], a
	call Pack_InitGFX
	ret

.NoPokemon:
	ld hl, YouDontHaveAMonText
	call Pack_PrintTextNoScroll
	ret
.AnEggCantHoldAnItemText:
	text_far _AnEggCantHoldAnItemText
	text_end

QuitItemSubmenu:
	ret

BattlePack:
	ld hl, wOptions
	set NO_TEXT_SCROLL, [hl]
	call InitPackBuffers
.loop
	call JoyTextDelay
	ld a, [wJumptableIndex]
	bit JUMPTABLE_EXIT_F, a
	jr nz, .end
	call .RunJumptable
	call DelayFrame
	jr .loop

.end
	ld a, [wCurPocket]
	ld [wLastPocket], a
	ld hl, wOptions
	res NO_TEXT_SCROLL, [hl]
	ret

.RunJumptable:
	ld a, [wJumptableIndex]
	ld hl, .Jumptable
	call Pack_GetJumptablePointer
	jp hl

.Jumptable:
; entries correspond to PACKSTATE_* constants
	dw .InitGFX            ;  0
	dw .InitItemsPocket    ;  1
	dw .ItemsPocketMenu    ;  2
	dw .InitBallsPocket    ;  3
	dw .BallsPocketMenu    ;  4
	dw .InitKeyItemsPocket ;  5
	dw .KeyItemsPocketMenu ;  6
	dw .InitBerriesPocket  ;  7
	dw .BerriesPocketMenu  ;  8
	dw .InitMedicinePocket ;  9
	dw .MedicinePocketMenu ; 10
	dw Pack_QuitNoScript   ; 11
	dw Pack_QuitRunScript  ; 12

	.InitGFX:
	xor a
	ldh [hBGMapMode], a
	call Pack_InitGFX
	call Pack_PlaceCursor
	ld a, [wPackJumptableIndex]
	inc a
	ld [wJumptableIndex], a
	ret

	.InitItemsPocket:
	xor a ; ITEM_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

	.ItemsPocketMenu:
	ld b, PACKSTATE_INITMEDICINEPOCKET ; left
	ld c, PACKSTATE_INITBALLSPOCKET ; right
	jp Pack_ShellPocketMenu

	.InitKeyItemsPocket:
	ld a, KEY_ITEM_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

	.KeyItemsPocketMenu:
	ld b, PACKSTATE_INITBALLSPOCKET ; left
	ld c, PACKSTATE_INITBERRIESPOCKET ; right
	jp Pack_ShellPocketMenu

	.InitBerriesPocket:
	ld a, BERRY_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

	.BerriesPocketMenu:
	ld b, PACKSTATE_INITKEYITEMSPOCKET ; left
	ld c, PACKSTATE_INITMEDICINEPOCKET ; right
	jp Pack_ShellPocketMenu

	.InitBallsPocket:
	ld a, BALL_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

	.BallsPocketMenu:
	ld b, PACKSTATE_INITITEMSPOCKET ; left
	ld c, PACKSTATE_INITKEYITEMSPOCKET ; right
	jp Pack_ShellPocketMenu

	.InitMedicinePocket:
	ld a, MEDICINE_POCKET
	ld [wCurPocket], a
	jp Pack_InitPocketShell

	.MedicinePocketMenu:
	ld b, PACKSTATE_INITBERRIESPOCKET ; left
	ld c, PACKSTATE_INITITEMSPOCKET ; right
	jp Pack_ShellPocketMenu

ItemSubmenu:
	farcall CheckItemContext
	ld a, [wItemAttributeValue]
TMHMSubmenu:
	and a
	jr z, .NoUse
	ld hl, .UsableMenuHeader
	ld de, .UsableJumptable
	jr .proceed

.NoUse:
	ld hl, .UnusableMenuHeader
	ld de, .UnusableJumptable
.proceed
	push hl
	push de
	pop de
	pop hl
	push de
	call LoadMenuHeader
	call Pack_VerticalMenu
	call Pack_CloseWindow
	pop hl
	ret c
	ld a, [wMenuCursorY]
	dec a
	call Pack_GetJumptablePointer
	jp hl

.UsableMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 7, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .UsableMenuData
	db 1 ; default option

.UsableMenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 2 ; items
	db "USE@"
	db "QUIT@"

.UsableJumptable:
	dw .Use
	dw .Quit

.UnusableMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 9, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .UnusableMenuData
	db 1 ; default option

.UnusableMenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 1 ; items
	db "QUIT@"

.UnusableJumptable:
	dw .Quit

.Use:
	farcall CheckItemContext
	ld a, [wItemAttributeValue]
	ld hl, .ItemFunctionJumptable
	rst JumpTable
	ret

.ItemFunctionJumptable:
; entries correspond to ITEMMENU_* constants
	dw .Oak         ; ITEMMENU_NOUSE
	dw .Oak
	dw .Oak
	dw .Oak
	dw .Unused      ; ITEMMENU_CURRENT
	dw .BattleField ; ITEMMENU_PARTY
	dw .BattleOnly  ; ITEMMENU_CLOSE

.Oak:
	ld hl, OakThisIsntTheTimeText
	call Pack_PrintTextNoScroll
	ret

.Unused:
	call DoItemEffect
	ld a, [wItemEffectSucceeded]
	and a
	jr nz, .ReturnToBattle
	ret

.BattleField:
	call DoItemEffect
	ld a, [wItemEffectSucceeded]
	and a
	jr nz, .quit_run_script
	xor a
	ldh [hBGMapMode], a
	call Pack_InitGFX
	ret

.ReturnToBattle:
	call ClearBGPalettes
	jr .quit_run_script

.BattleOnly:
	call DoItemEffect
	ld a, [wItemEffectSucceeded]
	and a
	jr z, .Oak
	cp $2
	jr z, .didnt_use_item
.quit_run_script
	ld a, PACKSTATE_QUITRUNSCRIPT
	ld [wJumptableIndex], a
	ret

.didnt_use_item
	xor a
	ld [wItemEffectSucceeded], a
	ret
.Quit:
	ret

InitPackBuffers:
	xor a
	ld [wJumptableIndex], a
	; pocket id -> jumptable index
	ld a, [wLastPocket]
	cp NUM_POCKETS
	jr c, .valid_last_pocket
	xor a
.valid_last_pocket
	ld [wCurPocket], a
	inc a
	add a
	dec a
	ld [wPackJumptableIndex], a
	xor a ; FALSE
	ld [wPackUsedItem], a
	xor a
	ld [wSwitchItem], a
	call Pack_ResetOverflowItemIconOAMBuffers
	ret

DepositSellInitPackBuffers:
	xor a
	ldh [hBGMapMode], a
	ld [wJumptableIndex], a ; PACKSTATE_INITGFX
	ld [wPackJumptableIndex], a ; PACKSTATE_INITGFX
	ld [wCurPocket], a ; ITEM_POCKET
	ld [wPackUsedItem], a
	ld [wSwitchItem], a
	call Pack_ResetOverflowItemIconOAMBuffers
	call Pack_InitGFX
	ret

DepositSellPack:
.restore_screen
	ld a, [wPackUsedItem]
	and a
	jr z, .ready
	xor a
	ld [wPackUsedItem], a
	call Pack_RedrawCurrentPocketShell

.ready
	call Pack_PlaceCursor

.loop
	call JoyTextDelay
	ldh a, [hJoyPressed]
	bit B_PAD_B, a
	jr nz, .b_button
	bit B_PAD_A, a
	jr nz, .a_button
	ldh a, [hJoyLast]
	bit B_PAD_LEFT, a
	jr nz, .d_left
	bit B_PAD_RIGHT, a
	jr nz, .d_right
	bit B_PAD_UP, a
	jr nz, .d_up
	bit B_PAD_DOWN, a
	jr nz, .d_down
	call DelayFrame
	jr .loop

.a_button
	call Pack_SelectCurrentItem
	jp nc, .delay_loop
	ld a, PAD_A
	call MenuClickSound
	ld a, [wCurItem]
	ld [wMartItemID], a
	ld a, TRUE
	ld [wPackUsedItem], a
	and a
	ret

.b_button
	ld a, PAD_B
	call MenuClickSound
	call Pack_HideCursor
	xor a ; FALSE
	ld [wPackUsedItem], a
	and a
	ret

	.d_left
	call Pack_MoveCursorLeft
	jr nc, .place_cursor
	ld a, [wCurPocket]
	and a
	jr nz, .left_ok
	ld a, NUM_POCKETS
.left_ok
	dec a
	jr .switch_pocket

	.d_right
	call Pack_MoveCursorRight
	jr nc, .place_cursor
	ld a, [wCurPocket]
	inc a
	cp NUM_POCKETS
	jr c, .switch_pocket
	xor a

.switch_pocket
	ld [wCurPocket], a
	call Pack_HideCursor
	ld de, SFX_SWITCH_POCKETS
	call PlaySFX
	call Pack_RedrawCurrentPocketShell
	jr .delay_loop

.d_up
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	push af
	call Pack_MoveCursorUp
	call Pack_GetPocketScrollPointer
	ld b, [hl]
	pop af
	cp b
	jr z, .place_cursor
	call Pack_RedrawVisibleItemIconsPageUp
	call Pack_PlaceCursor
	call Pack_LoadPreviousCachedItemIconRow
	call Pack_LoadAdjacentItemIconOAMCaches
	jr .delay_loop

.d_down
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	push af
	call Pack_MoveCursorDown
	call Pack_GetPocketScrollPointer
	ld b, [hl]
	pop af
	cp b
	jr z, .place_cursor
	call Pack_RedrawVisibleItemIconsPageDown
	call Pack_PlaceCursor
	call Pack_LoadNextCachedItemIconRow
	call Pack_LoadAdjacentItemIconOAMCaches
	jr .delay_loop

.place_cursor
	call Pack_PlaceCursor
	call Pack_UpdateSelectedItemText

.delay_loop
	call DelayFrame
	jp .loop

	.RunJumptable:
	ld a, [wJumptableIndex]
	ld hl, .Jumptable
	call Pack_GetJumptablePointer
	jp hl

.Jumptable:
; entries correspond to *_POCKET constants
	dw .ItemsPocket
	dw .BallsPocket
	dw .KeyItemsPocket
	dw .BerriesPocket
	dw .MedicinePocket

.ItemsPocket:
	xor a ; ITEM_POCKET
	call InitPocket
	ld hl, PC_Mart_ItemsPocketMenuHeader
	call CopyMenuHeader
	ld a, [wItemsPocketCursor]
	ld [wMenuCursorPosition], a
	ld a, [wItemsPocketScrollPosition]
	ld [wMenuScrollPosition], a
	call ScrollingMenu
	ld a, [wMenuScrollPosition]
	ld [wItemsPocketScrollPosition], a
	ld a, [wMenuCursorY]
	ld [wItemsPocketCursor], a
	ret

.KeyItemsPocket:
	ld a, KEY_ITEM_POCKET
	call InitPocket
	ld hl, PC_Mart_KeyItemsPocketMenuHeader
	call CopyMenuHeader
	ld a, [wKeyItemsPocketCursor]
	ld [wMenuCursorPosition], a
	ld a, [wKeyItemsPocketScrollPosition]
	ld [wMenuScrollPosition], a
	call ScrollingMenu
	ld a, [wMenuScrollPosition]
	ld [wKeyItemsPocketScrollPosition], a
	ld a, [wMenuCursorY]
	ld [wKeyItemsPocketCursor], a
	ret

.BerriesPocket:
	ld a, BERRY_POCKET
	call InitPocket
	ld hl, PC_Mart_BerriesPocketMenuHeader
	call CopyMenuHeader
	ld a, [wBerriesPocketCursor]
	ld [wMenuCursorPosition], a
	ld a, [wBerriesPocketScrollPosition]
	ld [wMenuScrollPosition], a
	call ScrollingMenu
	ld a, [wMenuScrollPosition]
	ld [wBerriesPocketScrollPosition], a
	ld a, [wMenuCursorY]
	ld [wBerriesPocketCursor], a
	ret

.BallsPocket:
	ld a, BALL_POCKET
	call InitPocket
	ld hl, PC_Mart_BallsPocketMenuHeader
	call CopyMenuHeader
	ld a, [wBallsPocketCursor]
	ld [wMenuCursorPosition], a
	ld a, [wBallsPocketScrollPosition]
	ld [wMenuScrollPosition], a
	call ScrollingMenu
	ld a, [wMenuScrollPosition]
	ld [wBallsPocketScrollPosition], a
	ld a, [wMenuCursorY]
	ld [wBallsPocketCursor], a
	ret

.MedicinePocket:
	ld a, MEDICINE_POCKET
	call InitPocket
	ld hl, PC_Mart_MedicinePocketMenuHeader
	call CopyMenuHeader
	ld a, [wMedicinePocketCursor]
	ld [wMenuCursorPosition], a
	ld a, [wMedicinePocketScrollPosition]
	ld [wMenuScrollPosition], a
	call ScrollingMenu
	ld a, [wMenuScrollPosition]
	ld [wMedicinePocketScrollPosition], a
	ld a, [wMenuCursorY]
	ld [wMedicinePocketCursor], a
	ret

InitPocket:
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	ret

TutorialPack:
	call DepositSellInitPackBuffers
	ld a, [wInputType]
	or a
	jr z, .select_item
	farcall _DudeAutoInput_RightA

.select_item
	call DepositSellPack
	xor a ; FALSE
	ld [wPackUsedItem], a
	ret

Pack_JumptableNext:
	ld hl, wJumptableIndex
	inc [hl]
	ret

Pack_GetJumptablePointer:
	ld e, a
	ld d, 0
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret

Pack_QuitNoScript:
	ld hl, wJumptableIndex
	set JUMPTABLE_EXIT_F, [hl]
	xor a ; FALSE
	ld [wPackUsedItem], a
	ret

Pack_QuitRunScript:
	ld hl, wJumptableIndex
	set JUMPTABLE_EXIT_F, [hl]
	ld a, TRUE
	ld [wPackUsedItem], a
	ret

Pack_VerticalMenu:
	xor a
	ldh [hBGMapMode], a
	call MenuBox
	call Pack_PrepareItemSubmenuAttrs
	call UpdateSprites
	call PlaceVerticalMenuItems
	call Pack_CommitPopupTilemapAndAttrmap
	call CopyMenuData
	ld a, [wMenuDataFlags]
	bit STATICMENU_CURSOR_F, a
	jr z, .cancel
	call InitVerticalMenuCursor
	call StaticMenuJoypad
	call MenuClickSound
	bit B_PAD_B, a
	jr z, .okay

.cancel
	scf
	ret

.okay
	and a
	ret

Pack_MenuTextbox:
	push hl
	call LoadMenuTextbox
	pop hl
	jr Pack_PrintTextNoScroll

Pack_PrintTextNoScroll:
	ld a, [wOptions]
	push af
	set NO_TEXT_SCROLL, a
	ld [wOptions], a
	push hl
	call Pack_SetUpTextbox
	pop hl
	call BuenaPrintText
	call Pack_TransferTilemapAndAttrmap
	pop af
	ld [wOptions], a
	ret

Pack_SetUpTextbox:
	push hl
	call SpeechTextbox
	call Pack_PrepareTextboxAttrs
	call UpdateSprites
	call Pack_TransferTilemapAndAttrmap
	pop hl
	ret

Pack_PrepareTextboxAttrs:
	hlcoord TEXTBOX_X, TEXTBOX_Y, wAttrmap
	lb bc, TEXTBOX_HEIGHT, TEXTBOX_WIDTH
	xor a
	jp FillBoxWithByte

Pack_CloseWindow:
	push af
	call ExitMenu
	call Pack_CommitPopupTilemapAndAttrmap
	call UpdateSprites
	pop af
	ret

Pack_SelectQuantityToToss:
	ld hl, Pack_TossItem_MenuHeader
	call LoadMenuHeader
	ld a, 1
	ld [wItemQuantityChange], a

.loop
	call Pack_UpdateQuantityToTossDisplay
	call Pack_InterpretQuantityToTossJoypad
	jr nc, .loop
	cp -1
	jr nz, .okay
	scf
	ret

.okay
	and a
	ret

Pack_UpdateQuantityToTossDisplay:
	call MenuBox
	call Pack_PrepareItemSubmenuAttrs
	call MenuBoxCoord2Tile
	ld de, SCREEN_WIDTH + 1
	add hl, de
	ld [hl], '×'
	inc hl
	ld de, wItemQuantityChange
	lb bc, PRINTNUM_LEADINGZEROS | 1, 2
	call PrintNum
	jp Pack_CommitPopupTilemapAndAttrmap

Pack_InterpretQuantityToTossJoypad:
	call JoyTextDelay_ForcehJoyDown
	bit B_PAD_B, c
	jr nz, .b
	bit B_PAD_A, c
	jr nz, .a
	bit B_PAD_DOWN, c
	jr nz, .down
	bit B_PAD_UP, c
	jr nz, .up
	bit B_PAD_LEFT, c
	jr nz, .left
	bit B_PAD_RIGHT, c
	jr nz, .right
	and a
	ret

.b
	ld a, -1
	scf
	ret

.a
	ld a, 0
	scf
	ret

.down
	ld hl, wItemQuantityChange
	dec [hl]
	jr nz, .finish_down
	ld a, [wItemQuantity]
	ld [hl], a

.finish_down
	and a
	ret

.up
	ld hl, wItemQuantityChange
	inc [hl]
	ld a, [wItemQuantity]
	cp [hl]
	jr nc, .finish_up
	ld [hl], 1

.finish_up
	and a
	ret

.left
	ld a, [wItemQuantityChange]
	sub 10
	jr c, .load_1
	jr z, .load_1
	jr .finish_left

.load_1
	ld a, 1

.finish_left
	ld [wItemQuantityChange], a
	and a
	ret

.right
	ld a, [wItemQuantityChange]
	add 10
	ld b, a
	ld a, [wItemQuantity]
	cp b
	jr nc, .finish_right
	ld b, a

.finish_right
	ld a, b
	ld [wItemQuantityChange], a
	and a
	ret

Pack_TossItem_MenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 15, 9, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw NULL
	db 0 ; default option

Pack_SelectQuantityToSell:
	farcall GetItemPrice
	ld a, d
	ld [wBuySellItemPrice + 0], a
	ld a, e
	ld [wBuySellItemPrice + 1], a
	ld hl, Pack_SellItem_MenuHeader
	call LoadMenuHeader
	ld a, 1
	ld [wItemQuantityChange], a

.loop
	call Pack_UpdateQuantityToSellDisplay
	call Pack_InterpretQuantityToTossJoypad
	jr nc, .loop
	cp -1
	jr nz, .okay
	scf
	ret

.okay
	and a
	ret

Pack_UpdateQuantityToSellDisplay:
	call MenuBox
	call Pack_PrepareItemSubmenuAttrs
	call MenuBoxCoord2Tile
	ld de, SCREEN_WIDTH + 1
	add hl, de
	ld [hl], '×'
	inc hl
	ld de, wItemQuantityChange
	lb bc, PRINTNUM_LEADINGZEROS | 1, 2
	call PrintNum
	call Pack_DisplaySellingPrice
	jp Pack_CommitPopupTilemapAndAttrmap

Pack_DisplaySellingPrice:
	call Pack_MultiplySellPrice
	call Pack_HalveSellPrice
	; fallthrough

Pack_DisplaySellSubtotal:
	push hl
	ld hl, hMoneyTemp
	ldh a, [hProduct + 1]
	ld [hli], a
	ldh a, [hProduct + 2]
	ld [hli], a
	ldh a, [hProduct + 3]
	ld [hl], a
	pop hl
	inc hl
	ld de, hMoneyTemp
	lb bc, PRINTNUM_MONEY | 3, 6
	jp PrintNum

Pack_MultiplySellPrice:
	xor a
	ldh [hMultiplicand + 0], a
	ld a, [wBuySellItemPrice + 0]
	ldh [hMultiplicand + 1], a
	ld a, [wBuySellItemPrice + 1]
	ldh [hMultiplicand + 2], a
	ld a, [wItemQuantityChange]
	ldh [hMultiplier], a
	push hl
	call Multiply
	pop hl
	ret

Pack_HalveSellPrice:
	push hl
	ld hl, hProduct + 1
	ld a, [hl]
	srl a
	ld [hli], a
	ld a, [hl]
	rra
	ld [hli], a
	ld a, [hl]
	rra
	ld [hl], a
	pop hl
	ret

Pack_SellItem_MenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 15, SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1
	dw NULL
	db 0 ; default option

Pack_YesNoBox:
	lb bc, SCREEN_WIDTH - 6, 7
	push bc
	ld hl, YesNoMenuHeader
	call CopyMenuHeader
	pop bc
	ld a, b
	cp SCREEN_WIDTH - 1 - 5
	jr nz, .okay
	ld a, SCREEN_WIDTH - 1 - 5
	ld b, a

.okay
	ld a, b
	ld [wMenuBorderLeftCoord], a
	add 5
	ld [wMenuBorderRightCoord], a
	ld a, c
	ld [wMenuBorderTopCoord], a
	add 4
	ld [wMenuBorderBottomCoord], a
	call PushWindow
	call Pack_TwoOptionMenu
	push af
	ld c, $f
	call DelayFrames
	call Pack_CloseWindow
	pop af
	jr c, .no
	ld a, [wMenuCursorY]
	cp 2 ; no
	jr z, .no
	and a
	ret

.no
	ld a, 2
	ld [wMenuCursorY], a
	scf
	ret

Pack_TwoOptionMenu:
	jp Pack_VerticalMenu

Pack_CommitPopupTilemapAndAttrmap:
	call CGBOnly_CopyTilemapAtOnce
	xor a
	ldh [hBGMapMode], a
	ret

WaitBGMap_DrawPackGFX:
	call DrawPackGFX
	jr Pack_TransferTilemapAndAttrmap

Pack_TransferTilemapAndAttrmap:
	call HDMATransferTilemapAndAttrmap_Menu
	xor a
	ldh [hBGMapMode], a
	ret

DrawPackGFX:
	ld a, [wCurPocket]
	cp NUM_POCKETS
	jr c, .valid_pocket
	xor a
.valid_pocket
	ld e, a
	ld d, 0
	ld a, [wBattleType]
	cp BATTLETYPE_TUTORIAL
	jr z, .male_dude
	ld a, [wPlayerGender]
	bit PLAYERGENDER_FEMALE_F, a
	jr nz, .female
.male_dude
	ld hl, PackGFXPointers
	add hl, de
	add hl, de
	ld a, [hli]
	ld e, a
	ld d, [hl]
	ld hl, vTiles2 tile PACK_GFX_TILE
	lb bc, BANK(PackGFX), 15
	call Get2bppViaHDMA
	ret

.female
	farcall DrawKrisPackGFX
	ret

PackGFXPointers:
	dw PackGFX + (15 tiles) * 1 ; ITEM_POCKET
	dw PackGFX + (15 tiles) * 3 ; BALL_POCKET
	dw PackGFX + (15 tiles) * 0 ; KEY_ITEM_POCKET
	dw PackGFX + (15 tiles) * 2 ; BERRY_POCKET
	dw PackGFX + (15 tiles) * 4 ; MEDICINE_POCKET

Pack_InterpretJoypad:
	ld hl, wMenuJoypad
	ld a, [wSwitchItem]
	and a
	jp nz, .switching_item
	ld a, [hl]
	and PAD_A
	jr nz, .a_button
	ld a, [hl]
	and PAD_B
	jr nz, .b_button
	ld a, [hl]
	and PAD_LEFT
	jr nz, .d_left
	ld a, [hl]
	and PAD_RIGHT
	jr nz, .d_right
	ld a, [hl]
	and PAD_START
	jr nz, .start
	ld a, [hl]
	and PAD_SELECT
	jr nz, .select
	scf
	ret

.a_button
	and a
	ret

.b_button
	ld a, PACKSTATE_QUITNOSCRIPT
	ld [wJumptableIndex], a
	scf
	ret

.d_left
	ld a, b
	ld [wJumptableIndex], a
	ld [wPackJumptableIndex], a
	push de
	ld de, SFX_SWITCH_POCKETS
	call PlaySFX
	pop de
	scf
	ret

.d_right
	ld a, c
	ld [wJumptableIndex], a
	ld [wPackJumptableIndex], a
	push de
	ld de, SFX_SWITCH_POCKETS
	call PlaySFX
	pop de
	scf
	ret

.start
	ld a, [wScrollingMenuListSize]
	cp 2
	jr c, .no_sort
	ld hl, SortItemsText
	call Pack_MenuTextbox
	call Pack_YesNoBox
	push af
	call Pack_CloseWindow
	pop af
	jr c, .no_sort
	farcall SortItemsInBag
	jr nc, .no_sort
	call Pack_ResetSortedPocketPosition
	ld de, SFX_SWITCH_POKEMON
	call WaitPlaySFX
	ld de, SFX_SWITCH_POKEMON
	call WaitPlaySFX
.no_sort
	scf
	ret

.select
	farcall SwitchItemsInBag
	ld hl, AskItemMoveText
	call Pack_PrintTextNoScroll
	scf
	ret

.switching_item
	ld a, [hl]
	and PAD_A | PAD_SELECT
	jr nz, .place_insert
	ld a, [hl]
	and PAD_B
	jr nz, .end_switch
	scf
	ret

.place_insert
	farcall SwitchItemsInBag
	ld de, SFX_SWITCH_POKEMON
	call WaitPlaySFX
	ld de, SFX_SWITCH_POKEMON
	call WaitPlaySFX
.end_switch
	xor a
	ld [wSwitchItem], a
	scf
	ret

Pack_ResetSortedPocketPosition:
	ld a, [wCurPocket]
	cp NUM_POCKETS
	ret nc
	ld e, a
	ld d, 0
	ld hl, .cursor_order
	add hl, de
	ld e, [hl]
	ld d, 0
	ld hl, wItemsPocketCursor
	add hl, de
	ld [hl], 1
	ld hl, wItemsPocketScrollPosition
	add hl, de
	xor a
	ld [hl], a
	ret

.cursor_order
	db 0 ; ITEM_POCKET
	db 2 ; BALL_POCKET
	db 1 ; KEY_ITEM_POCKET
	db 3 ; BERRY_POCKET
	db 4 ; MEDICINE_POCKET

Pack_InitGFX:
	call Pack_InitGFXLayout
	call Pack_LoadColors
	call Pack_DrawShellNoCursor
	call Pack_LoadAdjacentItemIconRows
	call DrawPackGFX
	jr Pack_InitGFXEnable

Pack_InitGFX_NoColors:
	call Pack_InitGFXLayout
	call Pack_DrawShellNoCursor
	call Pack_LoadAdjacentItemIconRows
	call DrawPackGFX

Pack_InitGFXEnable:
	call Pack_CopyTilemapAndAttrmapLCDOff
	call EnableLCD
	ret

Pack_InitGFXLayout:
	call ClearBGPalettes
	call ClearSprites
	call DisableLCD
	call ClearTilemap
	call Pack_ClearAttrmap
	xor a
	ldh [rVBK], a
	call Pack_LoadSplitMenuGFX
	call Pack_LoadCurrentPocketNameGFX
	ld hl, PackTitleGFX
	ld de, vTiles2 tile PACK_TITLE_TILE
	ld bc, PACK_TITLE_TILES tiles
	ld a, BANK(PackTitleGFX)
	call FarCopyBytes
	ld hl, PackHeaderGFX
	ld de, vTiles2 tile PACK_HEADER_TILE
	ld bc, 1 tiles
	ld a, BANK(PackHeaderGFX)
	call FarCopyBytes
	ldh a, [rVBK]
	push af
	ld a, $1
	ldh [rVBK], a
	ld hl, PackBlankGFX
	ld de, vTiles2 tile PACK_BLANK_TILE
	ld bc, 1 tiles
	ld a, BANK(PackBlankGFX)
	call FarCopyBytes
	pop af
	ldh [rVBK], a
	ret

Pack_LoadSplitMenuGFX:
	ld hl, PackPocketNameUpperLeftGFX
	ld de, vTiles2 tile PACK_POCKET_NAME_UPPER_LEFT_TILE
	ld bc, 1 tiles
	ld a, BANK(PackPocketNameUpperLeftGFX)
	call FarCopyBytes
	ld hl, PackPocketNameUpperRightGFX
	ld de, vTiles2 tile PACK_POCKET_NAME_UPPER_RIGHT_TILE
	ld bc, 1 tiles
	ld a, BANK(PackPocketNameUpperRightGFX)
	call FarCopyBytes
	ld hl, PackPocketNameBottomLeftGFX
	ld de, vTiles2 tile PACK_POCKET_NAME_BOTTOM_LEFT_TILE
	ld bc, 1 tiles
	ld a, BANK(PackPocketNameBottomLeftGFX)
	call FarCopyBytes
	ld hl, PackPocketNameBottomRightGFX
	ld de, vTiles2 tile PACK_POCKET_NAME_BOTTOM_RIGHT_TILE
	ld bc, 1 tiles
	ld a, BANK(PackPocketNameBottomRightGFX)
	call FarCopyBytes
	ld hl, PackPocketNameUpperMiddleGFX
	ld de, vTiles2 tile PACK_POCKET_NAME_UPPER_MIDDLE_TILE
	ld bc, 1 tiles
	ld a, BANK(PackPocketNameUpperMiddleGFX)
	call FarCopyBytes
	ld hl, PackPocketNameBottomMiddleGFX
	ld de, vTiles2 tile PACK_POCKET_NAME_BOTTOM_MIDDLE_TILE
	ld bc, 1 tiles
	ld a, BANK(PackPocketNameBottomMiddleGFX)
	call FarCopyBytes
	ld hl, PackBorderGFX
	ld de, vTiles2 tile PACK_BORDER_TILE
	ld bc, 1 tiles
	ld a, BANK(PackBorderGFX)
	call FarCopyBytes
	ld hl, PackPocketSwitchGFX
	ld de, vTiles2 tile PACK_POCKET_SWITCH_TILE
	ld bc, 6 tiles
	ld a, BANK(PackPocketSwitchGFX)
	call FarCopyBytes
	ld hl, PackPocketSortGFX
	ld de, vTiles2 tile PACK_POCKET_SORT_TILE
	ld bc, 6 tiles
	ld a, BANK(PackPocketSortGFX)
	jp FarCopyBytes

Pack_LoadCurrentPocketNameGFX:
	ld a, [wCurPocket]
	cp NUM_POCKETS
	jr c, .got_pocket
	xor a

.got_pocket
	ld e, a
	ld d, 0
	ld hl, .pocket_gfx
	add hl, de
	add hl, de
	ld a, [hli]
	ld e, a
	ld d, [hl]
	ld hl, vTiles2 tile PACK_POCKET_NAME_TILE
	lb bc, BANK(PackGeneralPocketGFX), 5
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	call Get2bppViaHDMA
	pop af
	ldh [rVBK], a
	ret

.pocket_gfx
	dw PackGeneralPocketGFX
	dw PackBallsPocketGFX
	dw PackKeyItemsPocketGFX
	dw PackBerriesPocketGFX
	dw PackMedicinePocketGFX

Pack_ClearAttrmap:
	hlcoord 0, 0, wAttrmap
	ld bc, wAttrmapEnd - wAttrmap
	xor a
	jp ByteFill

Pack_CopyTilemapAndAttrmapLCDOff:
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	hlcoord 0, 0, wAttrmap
	ld de, vBGMap0
	call Pack_CopyScreenMapRows
	xor a
	ldh [rVBK], a
	hlcoord 0, 0
	ld de, vBGMap0
	call Pack_CopyScreenMapRows
	pop af
	ldh [rVBK], a
	ret

Pack_CopyScreenMapRows:
	ld b, SCREEN_HEIGHT
.row
	push bc
	ld c, SCREEN_WIDTH
.col
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .col
	ld a, e
	add TILEMAP_WIDTH - SCREEN_WIDTH
	ld e, a
	jr nc, .next
	inc d
.next
	pop bc
	dec b
	jr nz, .row
	ret

Pack_DrawShellNoCursor:
	call Pack_DrawShellBase
	call Pack_DrawVisibleItemIcons
	call Pack_DrawTextboxes
	jp Pack_PrintSelectedItemText

Pack_DrawShellNoCursor_BlankIcons:
	call Pack_DrawShellBase
	call Pack_ClearVisibleItemSlots
	call Pack_DrawTextboxes
	ret

Pack_DrawShellBase:
	hlcoord 0, 0
	lb bc, 3, SCREEN_WIDTH
	ld a, PACK_HEADER_TILE
	call FillBoxWithByte

	hlcoord 2, 3
	lb bc, 6, 16
	call ClearBox

	hlcoord 0, 3
	lb bc, 10, 2
	ld a, PACK_BORDER_TILE
	call FillBoxWithByte
	hlcoord 18, 3
	lb bc, 10, 2
	ld a, PACK_BORDER_TILE
	call FillBoxWithByte

	call DrawPocketName

	hlcoord 7, 0
	lb bc, 1, PACK_TITLE_TILES
	ld a, PACK_TITLE_TILE
	call Pack_PlaceTileBlock

	hlcoord 7, 1
	lb bc, 1, 6
	ld a, PACK_POCKET_SWITCH_TILE
	call Pack_PlaceTileBlock

	hlcoord 7, 2
	lb bc, 1, 6
	ld a, PACK_POCKET_SORT_TILE
	call Pack_PlaceTileBlock

	call PlacePackGFX
	ret

PlacePackGFX:
	hlcoord 15, 0
	ld a, PACK_GFX_TILE
	ld de, SCREEN_WIDTH - 5
	ld b, 3
.row
	ld c, 5
.column
	ld [hli], a
	inc a
	dec c
	jr nz, .column
	add hl, de
	dec b
	jr nz, .row
	ret

DrawPocketName:
	ld hl, .tilemap
	ld d, h
	ld e, l
	hlcoord 0, 0
	ld c, 3
.row
	ld b, 5
.col
	ld a, [de]
	inc de
	ld [hli], a
	dec b
	jr nz, .col
	ld a, c
	ld c, SCREEN_WIDTH - 5
	add hl, bc
	ld c, a
	dec c
	jr nz, .row
	ret

.tilemap
	db PACK_POCKET_NAME_UPPER_LEFT_TILE
	db PACK_POCKET_NAME_UPPER_MIDDLE_TILE
	db PACK_POCKET_NAME_UPPER_MIDDLE_TILE
	db PACK_POCKET_NAME_UPPER_MIDDLE_TILE
	db PACK_POCKET_NAME_UPPER_RIGHT_TILE
	db PACK_POCKET_NAME_TILE + 0
	db PACK_POCKET_NAME_TILE + 1
	db PACK_POCKET_NAME_TILE + 2
	db PACK_POCKET_NAME_TILE + 3
	db PACK_POCKET_NAME_TILE + 4
	db PACK_POCKET_NAME_BOTTOM_LEFT_TILE
	db PACK_POCKET_NAME_BOTTOM_MIDDLE_TILE
	db PACK_POCKET_NAME_BOTTOM_MIDDLE_TILE
	db PACK_POCKET_NAME_BOTTOM_MIDDLE_TILE
	db PACK_POCKET_NAME_BOTTOM_RIGHT_TILE

Pack_DrawTextboxes:
	hlcoord 2, 9
	lb bc, 2, 14
	call Textbox
	hlcoord 0, 13
	lb bc, 3, 18
	jp Textbox

Pack_UpdateSelectedItemText:
	call Pack_PrintSelectedItemText
	jp Pack_TransferTilemapAndAttrmap

Pack_PrintSelectedItemText:
	call Pack_ClearSelectedItemText
	call Pack_SelectCurrentItem
	ret nc
	call Pack_PrintSelectedItemName
	call Pack_PrintSelectedItemQuantity
	jp Pack_PrintSelectedItemDescription

Pack_ClearSelectedItemText:
	hlcoord 3, 10
	lb bc, 2, 14
	call ClearBox
	hlcoord 1, 14
	lb bc, 3, 18
	jp ClearBox

Pack_PrintSelectedItemName:
	ld a, [wCurItem]
	ld [wNamedObjectIndex], a
	call GetItemName
	hlcoord 3, 10
	jp PlaceString

Pack_PrintSelectedItemQuantity:
	call Pack_GetCurrentPocketListPointer
	ld a, c
	cp 1
	ret z
	hlcoord 14, 11
	ld [hl], '×'
	hlcoord 15, 11
	ld de, wMenuSelectionQuantity
	lb bc, PRINTNUM_LEADINGZEROS | 1, 2
	jp PrintNum

Pack_PrintSelectedItemDescription:
	ld a, [wCurItem]
	ld [wCurSpecies], a
	decoord 1, 14
	farcall PrintItemDescription
	ret

Pack_PlaceTileBlock:
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

PackCursorPositions:
	db 16, 32
	db 48, 32
	db 80, 32
	db 112, 32
	db 16, 56
	db 48, 56
	db 80, 56
	db 112, 56

PackCursorTileCoords:
	db 2, 4
	db 6, 4
	db 10, 4
	db 14, 4
	db 2, 7
	db 6, 7
	db 10, 7
	db 14, 7

PackItemIconCoords:
	db 3, 3
	db 7, 3
	db 11, 3
	db 15, 3
	db 3, 6
	db 7, 6
	db 11, 6
	db 15, 6

PackItemIconVRAMDestinations:
	dw vTiles2 tile $00
	dw vTiles2 tile $09
	dw vTiles2 tile $12
	dw vTiles2 tile $1b
	dw vTiles2 tile $24
	dw vTiles2 tile $2d
	dw vTiles2 tile $36
	dw vTiles2 tile $3f
	dw vTiles2 tile $48
	dw vTiles2 tile $51
	dw vTiles2 tile $5a
	dw vTiles2 tile $63
	dw vTiles1 tile (PACK_ITEM_ICON_SIGNED_DEST_TILE + 0 * PACK_ITEM_ICON_TILES)
	dw vTiles1 tile (PACK_ITEM_ICON_SIGNED_DEST_TILE + 1 * PACK_ITEM_ICON_TILES)
	dw vTiles1 tile (PACK_ITEM_ICON_SIGNED_DEST_TILE + 2 * PACK_ITEM_ICON_TILES)
	dw vTiles1 tile (PACK_ITEM_ICON_SIGNED_DEST_TILE + 3 * PACK_ITEM_ICON_TILES)

PackItemIconFirstTiles:
	db $00
	db $09
	db $12
	db $1b
	db $24
	db $2d
	db $36
	db $3f
	db $48
	db $51
	db $5a
	db $63
	db PACK_ITEM_ICON_SIGNED_FIRST_TILE + 0 * PACK_ITEM_ICON_TILES
	db PACK_ITEM_ICON_SIGNED_FIRST_TILE + 1 * PACK_ITEM_ICON_TILES
	db PACK_ITEM_ICON_SIGNED_FIRST_TILE + 2 * PACK_ITEM_ICON_TILES
	db PACK_ITEM_ICON_SIGNED_FIRST_TILE + 3 * PACK_ITEM_ICON_TILES

Pack_DrawVisibleItemIcons:
	call Pack_NormalizeCursorPosition
	call Pack_PrepareVisibleItemIconPalettes
	jr Pack_DrawVisibleItemIconsAfterPalettes

Pack_DrawVisibleItemIconsDeferredOAM:
	call Pack_NormalizeCursorPosition
	xor a ; PACK_ITEM_ICON_OVERFLOW_SLOT_PAGE_UP
	call Pack_BuildVisibleItemIconPaletteState
	call Pack_LoadOverflowItemIconOAMHidden
	; fallthrough

Pack_DrawVisibleItemIconsAfterPalettes:
	xor a

.loop
	cp PACK_VISIBLE_ITEMS
	ret nc
	push af
	call Pack_GetVisibleSlotItem
	jr nc, .clear
	call GetPackItemIcon
	pop af
	push af
	call Pack_LoadItemIconGFXToSlot
	pop af
	push af
	call Pack_DrawItemIconTilemapForSlot
	pop af
	push af
	call Pack_DrawItemIconAttrmapForSlot
	pop af
	jr .next

.clear
	pop af
	push af
	call Pack_ClearVisibleItemSlot
	pop af

.next
	inc a
	jr .loop

Pack_RedrawVisibleItemIcons:
	call Pack_DrawVisibleItemIcons
	call Pack_TransferTilemapAndAttrmap
	jp Pack_LoadAdjacentItemIconRows

Pack_RedrawCurrentPocketAfterSort:
	call Pack_HideCursor
	call Pack_DrawShellNoCursor_BlankIcons
	call DrawPackGFX
	call Pack_HideOverflowItemIconOAM
	call Pack_TransferTilemapAndAttrmap
	call Pack_DrawVisibleItemIconsDeferredOAM
	call Pack_ApplyVisibleItemIconPalettes
	call Pack_PrintSelectedItemText
	call Pack_TransferTilemapAndAttrmap
	call Pack_ShowOverflowItemIconOAM
	call Pack_PlaceCursor
	jp Pack_LoadAdjacentItemIconRows

Pack_RedrawVisibleItemIconsPageUp:
	call Pack_DrawVisibleItemIconTilemapsPageUp
	call Pack_PrintSelectedItemText
	call Pack_TransferTilemapAndAttrmap
	call Pack_ApplyVisibleItemIconPalettes
	jp Pack_UsePreviousOverflowItemIconOAMCache

Pack_RedrawVisibleItemIconsPageDown:
	call Pack_DrawVisibleItemIconTilemapsPageDown
	call Pack_PrintSelectedItemText
	call Pack_TransferTilemapAndAttrmap
	call Pack_ApplyVisibleItemIconPalettes
	jp Pack_UseNextOverflowItemIconOAMCache

Pack_LoadAdjacentItemIconRows:
	call Pack_LoadPreviousCachedItemIconRow
	call Pack_LoadNextCachedItemIconRow
	jp Pack_LoadAdjacentItemIconOAMCaches

Pack_LoadPreviousCachedItemIconRow:
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	sub PACK_ROW_LENGTH
	ret c
	jr Pack_LoadItemIconRowAtAbsoluteSlot

Pack_LoadNextCachedItemIconRow:
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	add PACK_VISIBLE_ITEMS
; fallthrough

Pack_LoadItemIconRowAtAbsoluteSlot:
	ld b, a
	ld c, PACK_ROW_LENGTH

.loop
	ld a, b
	push bc
	push af
	call Pack_GetAbsoluteSlotItem
	jr nc, .no_item
	call GetPackItemIcon
	pop af
	call Pack_LoadItemIconGFXToAbsoluteSlot
	jr .next

.no_item
	pop af

.next
	pop bc
	inc b
	dec c
	jr nz, .loop
	ret

Pack_DrawVisibleItemIconTilemaps:
	call Pack_PrepareVisibleItemIconPalettes
	jr Pack_DrawVisibleItemIconTilemapsAfterPalettes

Pack_DrawVisibleItemIconTilemapsPageUp:
	xor a ; PACK_ITEM_ICON_OVERFLOW_SLOT_PAGE_UP
	call Pack_BuildVisibleItemIconPaletteState
	jr Pack_DrawVisibleItemIconTilemapsAfterPalettes

Pack_DrawVisibleItemIconTilemapsPageDown:
	ld a, PACK_ITEM_ICON_OVERFLOW_SLOT_PAGE_DOWN
	call Pack_BuildVisibleItemIconPaletteState

Pack_DrawVisibleItemIconTilemapsAfterPalettes:
	xor a

.loop
	cp PACK_VISIBLE_ITEMS
	ret nc
	push af
	call Pack_GetVisibleSlotItem
	jr nc, .clear
	pop af
	push af
	call Pack_DrawItemIconTilemapForSlot
	pop af
	push af
	call Pack_DrawItemIconAttrmapForSlot
	pop af
	jr .next

.clear
	pop af
	push af
	call Pack_ClearVisibleItemSlot
	pop af

.next
	inc a
	jr .loop

Pack_PrepareVisibleItemIconPalettes:
	xor a ; PACK_ITEM_ICON_OVERFLOW_SLOT_PAGE_UP
	call Pack_BuildVisibleItemIconPaletteState
	call Pack_LoadOverflowItemIconOAM
	jp Pack_ApplyVisibleItemIconPalettes

Pack_PrepareVisibleItemIconPalettesNoOAM:
	call Pack_BuildVisibleItemIconPaletteState
	jp Pack_ApplyVisibleItemIconPalettes

Pack_BuildVisibleItemIconPaletteState:
	push af
	call Pack_ClearItemIconPaletteState
	ldh a, [hCGB]
	and a
	jr z, .done
	call Pack_CountVisibleItemIconPalettes
	pop af
	call Pack_SelectOverflowItemIconSlot
	jp Pack_AssignVisibleItemIconPalettes

.done
	pop af
	ret

Pack_ApplyVisibleItemIconPalettes:
	ldh a, [hCGB]
	and a
	ret z
	farcall ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

Pack_ClearItemIconPaletteState:
	xor a
	ld [wPackItemIconPaletteCount], a
	ld a, PACK_ITEM_ICON_NO_OVERFLOW
	ld [wPackItemIconOverflowSlot], a
; fallthrough

Pack_ResetItemIconPaletteAssignments:
	xor a
	ld [wPackItemIconPaletteCount], a
	ld hl, wPackItemIconPaletteAttrs
	ld b, PACK_VISIBLE_ITEMS
	ld a, BG_BANK1 | PACK_ITEM_ICON_FIRST_PALETTE

.loop
	ld [hli], a
	dec b
	jr nz, .loop
	ret

Pack_InvalidateItemIconPaletteRecords:
	xor a
	ld [wPackItemIconPaletteCount], a
	ld hl, wPackItemIconPaletteRecords
	ld bc, (PACK_ITEM_ICON_PALETTES + 1) * PACK_ITEM_ICON_RECORD_SIZE
	call ByteFill
	ld a, PACK_ITEM_ICON_NO_OVERFLOW
	ld [wPackItemIconOverflowSlot], a
	ret

Pack_CountVisibleItemIconPalettes:
	xor a

.loop
	cp PACK_VISIBLE_ITEMS
	ret nc
	push af
	call Pack_GetVisibleSlotPalette
	jr nc, .next
	call Pack_FindItemIconPaletteRecord
	jr c, .next
	call Pack_AddItemIconPaletteRecord

.next
	pop af
	inc a
	jr .loop
	ret

Pack_SelectOverflowItemIconSlot:
	ld c, a
	ld a, [wPackItemIconPaletteCount]
	cp PACK_VISIBLE_ITEMS
	jr nz, .none
	ld a, c
	push bc
	call Pack_GetVisibleSlotItem
	pop bc
	jr nc, .none
	ld a, c
	jr .done

.none
	ld a, PACK_ITEM_ICON_NO_OVERFLOW

.done
	ld [wPackItemIconOverflowSlot], a
	ret

Pack_AssignVisibleItemIconPalettes:
	call Pack_ResetItemIconPaletteAssignments
	xor a

.loop
	cp PACK_VISIBLE_ITEMS
	ret nc
	push af
	ld c, a
	ld a, [wPackItemIconOverflowSlot]
	cp c
	jr z, .fallback
	ld a, c
	call Pack_GetVisibleSlotPalette
	jr nc, .fallback
	call Pack_FindItemIconPaletteRecord
	jr c, .existing
	call Pack_AddItemIconPaletteRecord
	inc a
	ld c, a
	push bc
	push de
	ld h, d
	ld l, e
	ld a, b
	call Pack_CopyItemIconBGPalette
	pop de
	pop bc
	jr .store

.existing
	inc a
	ld c, a
	jr .store

.fallback
	ld c, PACK_ITEM_ICON_FIRST_PALETTE

.store
	pop af
	push af
	call Pack_SetItemIconPaletteAttrForSlot
	pop af
	inc a
	jr .loop

Pack_GetVisibleSlotPalette:
	call Pack_GetVisibleSlotItem
	ret nc
	call GetPackItemIcon
	ld d, h
	ld e, l
	scf
	ret

Pack_FindItemIconPaletteRecord:
	ld hl, wPackItemIconPaletteRecords
	ld c, 0

.loop
	ld a, [wPackItemIconPaletteCount]
	cp c
	jr z, .not_found
	push hl
	ld a, [hli]
	cp b
	jr nz, .record_checked
	ld a, [hli]
	cp e
	jr nz, .record_checked
	ld a, [hl]
	cp d
	jr nz, .record_checked
	pop hl
	ld a, c
	scf
	ret

.record_checked
	pop hl
	inc hl
	inc hl
	inc hl
	inc c
	jr .loop

.not_found
	and a
	ret

Pack_AddItemIconPaletteRecord:
	push bc
	push de
	ld a, [wPackItemIconPaletteCount]
	pop de
	pop bc
	push af
	push bc
	call Pack_WriteItemIconPaletteRecord
	pop bc
	pop af
	push af
	inc a
	ld [wPackItemIconPaletteCount], a
	pop af
	ret

Pack_WriteItemIconPaletteRecord:
	push af
	ld a, b
	ldh [hTempBank], a
	pop af
	push de
	ld c, a
	add a
	add c
	ld c, a
	ld b, 0
	ld hl, wPackItemIconPaletteRecords
	add hl, bc
	ldh a, [hTempBank]
	ld [hli], a
	pop de
	ld a, e
	ld [hli], a
	ld a, d
	ld [hl], a
	ret

Pack_CopyItemIconBGPalette:
	ldh [hTempBank], a
	push hl
	ld a, c
	call Pack_GetBGPals1PaletteDestination
	pop hl
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rWBK], a
	ld bc, 1 palettes
	ldh a, [hTempBank]
	call FarCopyBytes
	pop af
	ldh [rWBK], a
	ret

Pack_GetBGPals1PaletteDestination:
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wBGPals1
	add hl, de
	ld d, h
	ld e, l
	ret

Pack_SetItemIconPaletteAttrForSlot:
	ld hl, wPackItemIconPaletteAttrs
	ld e, a
	ld d, 0
	add hl, de
	ld a, c
	or BG_BANK1
	ld [hl], a
	ret

Pack_LoadOverflowItemIconOAM:
	call Pack_LoadOverflowItemIconOAMHidden
	jp Pack_ShowOverflowItemIconOAM

Pack_LoadOverflowItemIconOAMHidden:
	ld a, [wPackItemIconOverflowSlot]
	cp PACK_ITEM_ICON_NO_OVERFLOW
	jp z, Pack_HideOverflowItemIconOAM
	call Pack_GetVisibleSlotItem
	jp nc, Pack_HideOverflowItemIconOAM
	call GetPackItemIcon
	ld a, [wPackItemIconOAMBuffer]
	ld c, a
	call Pack_LoadResolvedOverflowItemIconOAMToBuffer
	ret

Pack_LoadAdjacentItemIconOAMCaches:
	call Pack_LoadPreviousOverflowItemIconOAMCache
	jp Pack_LoadNextOverflowItemIconOAMCache

Pack_LoadPreviousOverflowItemIconOAMCache:
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	sub PACK_ROW_LENGTH
	ret c
	ld c, a
	ld a, [wPackItemIconOAMPreviousBuffer]
	ld b, a
	ld a, c
	ld c, b
	jr Pack_LoadOverflowItemIconOAMCacheAtAbsoluteSlot

Pack_LoadNextOverflowItemIconOAMCache:
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	add PACK_VISIBLE_ITEMS
	ld c, a
	ld a, [wPackItemIconOAMNextBuffer]
	ld b, a
	ld a, c
	ld c, b
	; fallthrough

Pack_LoadOverflowItemIconOAMCacheAtAbsoluteSlot:
	ldh [hTemp], a
	ld a, c
	push af
	ldh a, [hTemp]
	call Pack_GetAbsoluteSlotItem
	jr nc, .no_item
	call GetPackItemIcon
	pop af
	ld c, a
	jr Pack_LoadResolvedOverflowItemIconOAMToBuffer

.no_item
	pop af
	ret

Pack_LoadResolvedOverflowItemIconOAMToBuffer:
	push bc
	push hl
	ld a, c
	call Pack_GetOverflowItemIconVRAMDestinationForBuffer
	ld c, PACK_ITEM_ICON_TILES
	ldh a, [hBGMapMode]
	push af
	xor a
	ldh [hBGMapMode], a
	ldh a, [rVBK]
	push af
	ld a, $1
	ldh [rVBK], a
	call Get2bppViaHDMA
	pop af
	ldh [rVBK], a
	pop af
	ldh [hBGMapMode], a
	pop hl
	pop bc
	ld a, b
	jp Pack_CopyItemIconOBJPaletteToBuffer

Pack_CopyItemIconOBJPaletteToBuffer:
	ldh [hTempBank], a
	push hl
	ld a, c
	call Pack_GetOverflowItemIconOBPaletteDestinationForBuffer
	pop hl
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld bc, 1 palettes
	ldh a, [hTempBank]
	call FarCopyBytes
	pop af
	ldh [rWBK], a
	ret

Pack_UsePreviousOverflowItemIconOAMCache:
	ld a, [wPackItemIconOAMPreviousBuffer]
	ld [wPackItemIconOAMBuffer], a
	call Pack_ReassignAdjacentOverflowItemIconOAMBuffers
	jr Pack_ShowOverflowItemIconOAM

Pack_UseNextOverflowItemIconOAMCache:
	ld a, [wPackItemIconOAMNextBuffer]
	ld [wPackItemIconOAMBuffer], a
	call Pack_ReassignAdjacentOverflowItemIconOAMBuffers
	; fallthrough

Pack_ShowOverflowItemIconOAM:
	ld a, [wPackItemIconOverflowSlot]
	cp PACK_ITEM_ICON_NO_OVERFLOW
	jp z, Pack_HideOverflowItemIconOAM
	jp Pack_PlaceOverflowItemIconOAM

Pack_ResetOverflowItemIconOAMBuffers:
	xor a
	ld [wPackItemIconOAMBuffer], a
	inc a
	ld [wPackItemIconOAMPreviousBuffer], a
	inc a
	ld [wPackItemIconOAMNextBuffer], a
	ret

Pack_ReassignAdjacentOverflowItemIconOAMBuffers:
	ld a, [wPackItemIconOAMBuffer]
	and a
	jr z, .current_zero
	cp 1
	jr z, .current_one
	xor a
	ld [wPackItemIconOAMPreviousBuffer], a
	inc a
	ld [wPackItemIconOAMNextBuffer], a
	ret

.current_zero
	ld a, 1
	ld [wPackItemIconOAMPreviousBuffer], a
	inc a
	ld [wPackItemIconOAMNextBuffer], a
	ret

.current_one
	xor a
	ld [wPackItemIconOAMPreviousBuffer], a
	ld a, 2
	ld [wPackItemIconOAMNextBuffer], a
	ret

Pack_GetOverflowItemIconVRAMDestinationForBuffer:
	and a
	ld hl, vTiles1 tile PACK_ITEM_ICON_OAM_DEST_TILE
	ret z
	cp 1
	ld hl, vTiles1 tile PACK_ITEM_ICON_OAM_SECOND_DEST_TILE
	ret z
	ld hl, vTiles1 tile PACK_ITEM_ICON_OAM_THIRD_DEST_TILE
	ret

Pack_GetOverflowItemIconOAMFirstTileForBuffer:
	and a
	jr z, .first
	cp 1
	jr z, .second
	ld a, PACK_ITEM_ICON_OAM_THIRD_FIRST_TILE
	ret

.first
	ld a, PACK_ITEM_ICON_OAM_FIRST_TILE
	ret

.second
	ld a, PACK_ITEM_ICON_OAM_SECOND_FIRST_TILE
	ret

Pack_GetOverflowItemIconOAMPaletteForBuffer:
	and a
	jr z, .first
	cp 1
	jr z, .second
	ld a, PACK_ITEM_ICON_OAM_THIRD_PALETTE
	ret

.first
	ld a, PACK_ITEM_ICON_OAM_FIRST_PALETTE
	ret

.second
	ld a, PACK_ITEM_ICON_OAM_SECOND_PALETTE
	ret

Pack_GetOverflowItemIconOBPaletteDestinationForBuffer:
	and a
	ld de, wOBPals1 palette PACK_ITEM_ICON_OAM_FIRST_PALETTE
	ret z
	cp 1
	ld de, wOBPals1 palette PACK_ITEM_ICON_OAM_SECOND_PALETTE
	ret z
	ld de, wOBPals1 palette PACK_ITEM_ICON_OAM_THIRD_PALETTE
	ret

Pack_PlaceOverflowItemIconOAM:
	call Pack_GetItemIconCoord
	ld a, c
	add a
	add a
	add a
	add 8
	ld c, a
	ld a, b
	add a
	add a
	add a
	add 16
	ld b, a
	ld hl, wShadowOAMSprite01
	ld a, [wPackItemIconOAMBuffer]
	call Pack_GetOverflowItemIconOAMFirstTileForBuffer
	ld d, a
	ld a, [wPackItemIconOAMBuffer]
	call Pack_GetOverflowItemIconOAMPaletteForBuffer
	or OAM_BANK1
	ld e, a
	call .row
	ld a, b
	add 8
	ld b, a
	call .row
	ld a, b
	add 8
	ld b, a

.row
	ld a, b
	ld [hli], a
	ld a, c
	ld [hli], a
	ld a, d
	ld [hli], a
	inc d
	ld a, e
	ld [hli], a
	ld a, b
	ld [hli], a
	ld a, c
	add 8
	ld [hli], a
	ld a, d
	ld [hli], a
	inc d
	ld a, e
	ld [hli], a
	ld a, b
	ld [hli], a
	ld a, c
	add 16
	ld [hli], a
	ld a, d
	ld [hli], a
	inc d
	ld a, e
	ld [hli], a
	ret

Pack_HideOverflowItemIconOAM:
	ld hl, wShadowOAMSprite01YCoord
	ld de, OBJ_SIZE
	ld b, PACK_ITEM_ICON_TILES
	xor a

.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	ret

Pack_ClearVisibleItemSlots:
	xor a

.loop
	cp PACK_VISIBLE_ITEMS
	ret nc
	push af
	call Pack_ClearVisibleItemSlot
	pop af
	inc a
	jr .loop

Pack_LoadItemIconGFXToSlot:
	push bc
	push de
	call Pack_GetItemIconPhysicalSlot
	jr Pack_LoadItemIconGFXToPhysicalSlot_WithSource

Pack_LoadItemIconGFXToAbsoluteSlot:
	push bc
	push de
	call Pack_GetItemIconPhysicalSlotForAbsoluteSlot
; fallthrough

Pack_LoadItemIconGFXToPhysicalSlot_WithSource:
	push af
	call Pack_GetItemIconVRAMDestination
	pop af
	call Pack_GetItemIconVRAMBank
	ldh [hTempBank], a
	pop de
	pop bc
	ld c, PACK_ITEM_ICON_TILES
	ldh a, [hBGMapMode]
	push af
	xor a
	ldh [hBGMapMode], a
	ldh a, [rVBK]
	push af
	ldh a, [hTempBank]
	ldh [rVBK], a
	call Get2bppViaHDMA
	pop af
	ldh [rVBK], a
	pop af
	ldh [hBGMapMode], a
	ret

Pack_DrawItemIconTilemapForSlot:
	push af
	call Pack_GetItemIconCoord
	call Coord2Tile
	pop af
	push hl
	call Pack_GetItemIconPhysicalSlot
	call Pack_GetItemIconFirstTile
	pop hl
	jp PlacePackItemIconTiles

Pack_DrawItemIconAttrmapForSlot:
	push af
	call Pack_GetItemIconCoord
	call Coord2Attr
	pop af
	push hl
	call Pack_GetItemIconAttr
	pop hl
	lb bc, 3, 3
	jp FillBoxWithByte

Pack_ClearVisibleItemSlot:
	push af
	call Pack_GetItemIconCoord
	call Coord2Tile
	lb bc, 3, 3
	ld a, PACK_BLANK_TILE
	call FillBoxWithByte
	pop af
	call Pack_GetItemIconCoord
	call Coord2Attr
	lb bc, 3, 3
	ld a, BG_BANK1 | PACK_ITEM_ICON_FIRST_PALETTE
	jp FillBoxWithByte

Pack_GetItemIconCoord:
	ld hl, PackItemIconCoords
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld c, [hl]
	inc hl
	ld b, [hl]
	ret

Pack_GetItemIconVRAMDestination:
	ld hl, PackItemIconVRAMDestinations
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret

Pack_GetItemIconPhysicalSlot:
	ld c, a
	call Pack_GetPocketScrollPointer
	ld a, [hl]
	add c

Pack_GetItemIconPhysicalSlotForAbsoluteSlot:
	ld c, a
	and PACK_ROW_LENGTH - 1
	ld b, a
	ld a, c
	srl a
	srl a

.mod
	cp PACK_ICON_ROW_BUFFERS
	jr c, .got_row
	sub PACK_ICON_ROW_BUFFERS
	jr .mod

.got_row
	add a
	add a
	add b
	ret

Pack_GetItemIconFirstTile:
	ld hl, PackItemIconFirstTiles
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [hl]
	ret

Pack_GetItemIconVRAMBank:
	ld a, 1
	ret

Pack_GetItemIconAttr:
	ld hl, wPackItemIconPaletteAttrs
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [hl]
	ret

UpdatePackItemIcon:
	ld a, [wMenuSelection]
	cp -1
	jr z, ShowPackItemEmptyIcon
	call PlacePackItemIcon
	ld a, [wMenuSelection]
	call GetPackItemIcon
	jr LoadPackItemIcon

GetPackItemIcon:
	ld c, a
	cp TM01
	jr c, .search_table
	ld b, BANK(PackItemTMHMIconGFX)
	ld de, PackItemTMHMIconGFX
	ld hl, PackItemTMHMIconPalette
	ret

.search_table
	ld hl, PackItemIconTable
	ld b, BANK(PackItemQuestionIconGFX)
	call SearchPackItemIconTable
	ret c
	ld hl, PackItemGeneralIconTable
	ld b, BANK(PackItemGeneralIconGFX)
	call SearchPackItemIconTable
	ret c
	ld b, BANK(PackItemQuestionIconGFX)
	ld de, PackItemQuestionIconGFX
	ld hl, PackItemQuestionIconPalette
	ret

SearchPackItemIconTable:
.loop
	ld a, [hli]
	cp -1
	jr z, .not_found
	cp c
	jr z, .found
	inc hl
	inc hl
	inc hl
	inc hl
	jr .loop

.found
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, [hli]
	ld h, [hl]
	ld l, a
	scf
	ret

.not_found
	and a
	ret

ShowPackItemEmptyIcon:
	call PlacePackItemIcon
	ld b, BANK(PackItemEmptyIconGFX)
	ld de, PackItemEmptyIconGFX
	ld hl, PackItemEmptyIconPalette
	jr LoadPackItemIcon

LoadPackItemIcon:
	push bc
	push hl
	ld hl, vTiles2 tile PACK_ITEM_ICON_FIRST_TILE
	ld c, PACK_ITEM_ICON_TILES
	ldh a, [hCGB]
	and a
	jr z, .dmg
	call Get2bppViaHDMA
	jr .loaded

.dmg
	call Request2bpp

.loaded
	pop hl
	pop bc
	call LoadPackItemIconPalette
	ret

LoadPackItemIconPalette:
	ldh a, [hCGB]
	and a
	ret z
	ld a, b
	ldh [hTempBank], a
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rWBK], a
	ld de, wBGPals1 palette 6
	ld bc, 1 palettes
	ldh a, [hTempBank]
	call FarCopyBytes
	pop af
	ldh [rWBK], a
	farcall ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

HidePackItemIcon:
	jr ShowPackItemEmptyIcon

PlacePackItemIcon:
	hlcoord 1, 9
	ld a, PACK_ITEM_ICON_FIRST_TILE
	jr PlacePackItemIconTiles

PlacePackItemIconTiles:
	ld de, SCREEN_WIDTH - 3
	ld b, 3
.row
	ld c, 3
.column
	ld [hli], a
	inc a
	dec c
	jr nz, .column
	add hl, de
	dec b
	jr nz, .row
	ret

INCLUDE "gfx/items/items.asm"

Pack_GetItemName:
	ld a, [wCurItem]
	ld [wNamedObjectIndex], a
	call GetItemName
	call CopyName1
	ret

Pack_ClearTilemap: ; unreferenced
	hlcoord 0, 0
	ld bc, SCREEN_AREA
	ld a, ' '
	call ByteFill
	ret

ClearPocketList:
	hlcoord 5, 2
	lb bc, 10, SCREEN_WIDTH - 5
	call ClearBox
	ret

Pack_InitColors:
	call Pack_LoadColors
	call Pack_DrawShellNoCursor
	call HDMATransferTilemapAndAttrmap_Menu
	xor a
	ldh [hBGMapMode], a
	call DelayFrame
	ret

Pack_LoadColors:
	ld b, SCGB_PACKPALS
	call GetSGBLayout
	call SetDefaultBGPAndOBP
	call Pack_InvalidateItemIconPaletteRecords
	call Pack_LoadGrayItemPalette
	ret

Pack_LoadGrayItemPalette:
	ldh a, [hCGB]
	and a
	ret z
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rWBK], a
	ld de, wBGPals1 palette PACK_ITEM_ICON_FIRST_PALETTE
	ld b, PACK_ITEM_ICON_PALETTES

.loop
	push bc
	ld hl, PackGrayItemPalette
	ld bc, 1 palettes
	call CopyBytes
	pop bc
	dec b
	jr nz, .loop

	pop af
	ldh [rWBK], a
	farcall ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

PackGrayItemPalette:
	RGB 31, 31, 31
	RGB 20, 20, 20
	RGB 10, 10, 10
	RGB 00, 00, 00

ItemsPocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR | SCROLLINGMENU_ENABLE_START ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wNumItems
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

PC_Mart_ItemsPocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wNumItems
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

KeyItemsPocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR | SCROLLINGMENU_ENABLE_START ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_NORMAL ; item format
	dbw 0, wNumKeyItems
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

PC_Mart_KeyItemsPocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_NORMAL ; item format
	dbw 0, wNumKeyItems
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

BallsPocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR | SCROLLINGMENU_ENABLE_START ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wNumBalls
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

PC_Mart_BallsPocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wNumBalls
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

BerriesPocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR | SCROLLINGMENU_ENABLE_START ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wNumBerries
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

PC_Mart_BerriesPocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wNumBerries
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

MedicinePocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR | SCROLLINGMENU_ENABLE_START ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wNumMedicine
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

PC_Mart_MedicinePocketMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wNumMedicine
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

PackNoItemText: ; unreferenced
	text_far _PackNoItemText
	text_end

AskThrowAwayText:
	text_far _AskThrowAwayText
	text_end

AskQuantityThrowAwayText:
	text_far _AskQuantityThrowAwayText
	text_end

SortItemsText:
	text "Sort items"
	line "alphabetically?"
	done

NotEnoughItemsToSortText:
	text "Not enough items"
	line "to sort!"
	prompt

ThrewAwayText:
	text_far _ThrewAwayText
	text_end

OakThisIsntTheTimeText:
	text_far _OakThisIsntTheTimeText
	text_end

YouDontHaveAMonText:
	text_far _YouDontHaveAMonText
	text_end

RegisteredItemText:
	text_far _RegisteredItemText
	text_end

CantRegisterText:
	text_far _CantRegisterText
	text_end

AskItemMoveText:
	text_far _AskItemMoveText
	text_end

PackEmptyText:
	text_far _PackEmptyText
	text_end

YouCantUseItInABattleText: ; unreferenced
	text_far _YouCantUseItInABattleText
	text_end

SECTION "Pack Graphics", ROMX

PackPocketNameUpperLeftGFX:
INCBIN "gfx/pack/pocket_name_upper_left.2bpp"
PackPocketNameUpperMiddleGFX:
INCBIN "gfx/pack/pocket_name_upper_middle.2bpp"
PackPocketNameUpperRightGFX:
INCBIN "gfx/pack/pocket_name_upper_right.2bpp"
PackPocketNameBottomLeftGFX:
INCBIN "gfx/pack/pocket_name_bottom_left.2bpp"
PackPocketNameBottomMiddleGFX:
INCBIN "gfx/pack/pocket_name_bottom_middle.2bpp"
PackPocketNameBottomRightGFX:
INCBIN "gfx/pack/pocket_name_bottom_right.2bpp"
PackGeneralPocketGFX:
INCBIN "gfx/pack/general_pocket.2bpp"
PackBallsPocketGFX:
INCBIN "gfx/pack/balls_pocket.2bpp"
PackKeyItemsPocketGFX:
INCBIN "gfx/pack/key_items_pocket.2bpp"
PackBerriesPocketGFX:
INCBIN "gfx/pack/berries_pocket.2bpp"
PackMedicinePocketGFX:
INCBIN "gfx/pack/medicine_pocket.2bpp"
PackBorderGFX:
INCBIN "gfx/pack/pack_border.2bpp"
PackPocketSwitchGFX:
INCBIN "gfx/pack/pocket_switch.2bpp"
PackPocketSortGFX:
INCBIN "gfx/pack/pocket_sort.2bpp"
PackGFX:
INCBIN "gfx/pack/pack.2bpp"
PackTitleGFX:
INCBIN "gfx/pack/pack_title.2bpp"

PackHeaderGFX:
	rept 16
	db %11111111
	endr

PackBlankGFX:
	rept 16
	db %00000000
	endr

SECTION "Pack Other Item Icons", ROMX

INCLUDE "gfx/items/other_icons.asm"

PackItemQuestionIconGFX:
INCBIN "gfx/items/misc/placeholder.2bpp"
PackItemTMHMIconGFX:
INCBIN "gfx/items/tmhm/tmhm_static.2bpp"
PackItemEmptyIconGFX:
INCBIN "gfx/items/misc/empty_space.2bpp"
PackItemPokeBallIconGFX:
INCBIN "gfx/items/poke_balls/poke_ball.2bpp"
PackItemPotionIconGFX:
INCBIN "gfx/items/medicine/potion.2bpp"
PackItemAntidoteIconGFX:
INCBIN "gfx/items/medicine/antidote.2bpp"
PackItemMaxPotionIconGFX:
INCBIN "gfx/items/medicine/max_potion.2bpp"
PackItemFullHealIconGFX:
INCBIN "gfx/items/medicine/full_heal.2bpp"
PackItemReviveIconGFX:
INCBIN "gfx/items/medicine/revive.2bpp"
PackItemMaxReviveIconGFX:
INCBIN "gfx/items/medicine/max_revive.2bpp"
PackItemFreshWaterIconGFX:
INCBIN "gfx/items/medicine/fresh_water.2bpp"
PackItemSodaPopIconGFX:
INCBIN "gfx/items/medicine/soda_pop.2bpp"
PackItemLemonadeIconGFX:
INCBIN "gfx/items/medicine/lemonade.2bpp"
PackItemEtherIconGFX:
INCBIN "gfx/items/medicine/ether.2bpp"
PackItemMoomooMilkIconGFX:
INCBIN "gfx/items/medicine/moomoo_milk.2bpp"
PackItemEnergyPowderIconGFX:
INCBIN "gfx/items/medicine/energypowder.2bpp"
PackItemHealPowderIconGFX:
INCBIN "gfx/items/medicine/heal_powder.2bpp"
PackItemRevivalHerbIconGFX:
INCBIN "gfx/items/medicine/revival_herb.2bpp"
PackItemBerryJuiceIconGFX:
INCBIN "gfx/items/medicine/berry_juice.2bpp"
PackItemSacredAshIconGFX:
INCBIN "gfx/items/medicine/sacred_ash.2bpp"
PackItemMasterBallIconGFX:
INCBIN "gfx/items/poke_balls/master_ball.2bpp"
PackItemUltraBallIconGFX:
INCBIN "gfx/items/poke_balls/ultra_ball.2bpp"
PackItemGreatBallIconGFX:
INCBIN "gfx/items/poke_balls/great_ball.2bpp"
PackItemHeavyBallIconGFX:
INCBIN "gfx/items/poke_balls/heavy_ball.2bpp"
PackItemLevelBallIconGFX:
INCBIN "gfx/items/poke_balls/level_ball.2bpp"
PackItemLureBallIconGFX:
INCBIN "gfx/items/poke_balls/lure_ball.2bpp"
PackItemFastBallIconGFX:
INCBIN "gfx/items/poke_balls/fast_ball.2bpp"
PackItemFriendBallIconGFX:
INCBIN "gfx/items/poke_balls/friend_ball.2bpp"
PackItemMoonBallIconGFX:
INCBIN "gfx/items/poke_balls/moon_ball.2bpp"
PackItemLoveBallIconGFX:
INCBIN "gfx/items/poke_balls/love_ball.2bpp"
PackItemOranBerryIconGFX:
INCBIN "gfx/items/berries/oran_berry.2bpp"
PackItemPechaBerryIconGFX:
INCBIN "gfx/items/berries/pecha_berry.2bpp"
PackItemCheriBerryIconGFX:
INCBIN "gfx/items/berries/cheri_berry.2bpp"
PackItemAspearBerryIconGFX:
INCBIN "gfx/items/berries/aspear_berry.2bpp"
PackItemRawstBerryIconGFX:
INCBIN "gfx/items/berries/rawst_berry.2bpp"
PackItemPersimBerryIconGFX:
INCBIN "gfx/items/berries/persim_berry.2bpp"
PackItemChestoBerryIconGFX:
INCBIN "gfx/items/berries/chesto_berry.2bpp"
PackItemLumBerryIconGFX:
INCBIN "gfx/items/berries/lum_berry.2bpp"
PackItemLeppaBerryIconGFX:
INCBIN "gfx/items/berries/leppa_berry.2bpp"
PackItemSitrusBerryIconGFX:
INCBIN "gfx/items/berries/sitrus_berry.2bpp"

PackItemEnergyRootIconGFX:
INCBIN "gfx/items/medicine/energy_root.2bpp"
PackItemVitaminIconGFX:
INCBIN "gfx/items/medicine/hp_up.2bpp"
PackItemPPUpIconGFX:
INCBIN "gfx/items/medicine/pp_up.2bpp"
PackItemBicycleIconGFX:
INCBIN "gfx/items/key_items/bicycle.2bpp"
PackItemCoinCaseIconGFX:
INCBIN "gfx/items/key_items/coin_case.2bpp"
PackItemItemfinderIconGFX:
INCBIN "gfx/items/key_items/itemfinder.2bpp"
PackItemGoodRodIconGFX:
INCBIN "gfx/items/key_items/good_rod.2bpp"
PackItemOldRodIconGFX:
INCBIN "gfx/items/key_items/old_rod.2bpp"
PackItemSuperRodIconGFX:
INCBIN "gfx/items/key_items/super_rod.2bpp"
PackItemRedScaleIconGFX:
INCBIN "gfx/items/key_items/red_scale.2bpp"
PackItemSecretPotionIconGFX:
INCBIN "gfx/items/key_items/secretpotion.2bpp"
PackItemSSTicketIconGFX:
INCBIN "gfx/items/key_items/ss_ticket.2bpp"
PackItemMysteryEggIconGFX:
INCBIN "gfx/items/key_items/mystery_egg.2bpp"
PackItemClearBellIconGFX:
INCBIN "gfx/items/key_items/clear_bell.2bpp"
PackItemSilverWingIconGFX:
INCBIN "gfx/items/key_items/silver_wing.2bpp"
PackItemRageCandyBarIconGFX:
INCBIN "gfx/items/key_items/ragecandybar.2bpp"
PackItemGSBallIconGFX:
INCBIN "gfx/items/key_items/gs_ball.2bpp"
PackItemBlueCardIconGFX:
INCBIN "gfx/items/key_items/blue_card.2bpp"
PackItemMachinePartIconGFX:
INCBIN "gfx/items/key_items/machine_part.2bpp"
PackItemLostItemIconGFX:
INCBIN "gfx/items/key_items/lost_item.2bpp"
PackItemBasementKeyIconGFX:
INCBIN "gfx/items/key_items/basement_key.2bpp"
PackItemPassIconGFX:
INCBIN "gfx/items/key_items/pass.2bpp"
PackItemSquirtBottleIconGFX:
INCBIN "gfx/items/key_items/squirtbottle.2bpp"
PackItemRainbowWingIconGFX:
INCBIN "gfx/items/key_items/rainbow_wing.2bpp"
PackItemCardKeyIconGFX:
INCBIN "gfx/items/key_items/card_key.2bpp"
PackItemApricornBoxIconGFX:
INCBIN "gfx/items/key_items/apricorn_box.2bpp"
PackItemTMHMCaseIconGFX:
INCBIN "gfx/items/key_items/tmhm_case.2bpp"
PackItemApricornIconGFX:
INCBIN "gfx/items/apricorns/red_apricorn.2bpp"

SECTION "Pack General Item Icons", ROMX

INCLUDE "gfx/items/general_icons.asm"
