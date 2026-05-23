Kurt_PrintTextWhichApricorn:
	ld hl, .WhichApricornText
	call PrintText
	ret

.WhichApricornText:
	text_far _WhichApricornText
	text_end

Kurt_PrintTextHowMany:
	ld hl, .HowManyShouldIMakeText
	call PrintText
	ret

.HowManyShouldIMakeText:
	text_far _HowManyShouldIMakeText
	text_end

SelectApricornForKurt:
	call LoadStandardMenuHeader
	ld c, $1
	xor a
	ld [wMenuScrollPosition], a
	ld [wKurtApricornQuantity], a
.loop
	push bc
	call Kurt_PrintTextWhichApricorn
	pop bc
	ld a, c
	ld [wMenuSelection], a
	call Kurt_SelectApricorn
	ld a, c
	ld [wScriptVar], a
	and a
	jr z, .done
	ld [wCurItem], a
	ld a, [wMenuCursorY]
	ld c, a
	push bc
	call Kurt_PrintTextHowMany
	call Kurt_SelectQuantity
	pop bc
	jr nc, .loop
	ld a, [wItemQuantityChange]
	ld [wKurtApricornQuantity], a
	call Kurt_GiveUpSelectedQuantityOfSelectedApricorn

.done
	call ExitMenu
	ret

Kurt_SelectApricorn:
	farcall FindApricornsInBag
	jr c, .nope
	ld hl, .MenuHeader
	call CopyMenuHeader
	ld a, [wMenuSelection]
	ld [wMenuCursorPosition], a
	xor a
	ldh [hBGMapMode], a
	call InitScrollingMenu
	call UpdateSprites
	call ScrollingMenu
	ld a, [wMenuJoypad]
	cp PAD_B
	jr z, .nope
	ld a, [wMenuSelection]
	cp -1
	jr nz, .done

.nope
	xor a ; FALSE

.done
	ld c, a
	ret

.MenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 1, 1, 13, 10
	dw .MenuData
	db 1 ; default option

	db 0 ; unused

.MenuData:
	db SCROLLINGMENU_DISPLAY_ARROWS ; flags
	db 4, 7 ; rows, columns
	db SCROLLINGMENU_ITEMS_NORMAL ; item format
	dbw 0, wKurtApricornCount
	dba .Name
	dba .Quantity
	dba NULL

.Name:
	ld a, [wMenuSelection]
	and a
	ret z
	farcall PlaceMenuItemName
	ret

.Quantity:
	ld a, [wMenuSelection]
	ld [wCurItem], a
	call Kurt_GetQuantityOfApricorn
	ret z
	ld a, [wItemQuantityChange]
	ld [wMenuSelectionQuantity], a
	farcall PlaceMenuItemQuantity
	ret

Kurt_SelectQuantity:
	ld a, [wCurItem]
	ld [wMenuSelection], a
	call Kurt_GetQuantityOfApricorn
	jr z, .done
	ld a, [wItemQuantityChange]
	ld [wItemQuantity], a
	ld a, $1
	ld [wItemQuantityChange], a
	ld hl, .MenuHeader
	call LoadMenuHeader
.loop
	xor a
	ldh [hBGMapMode], a
	call MenuBox
	call UpdateSprites
	call .PlaceApricornName
	call PlaceApricornQuantity
	call ApplyTilemap
	farcall Kurt_SelectQuantity_InterpretJoypad
	jr nc, .loop

	push bc
	call PlayClickSFX
	pop bc
	ld a, b
	cp -1
	jr z, .done
	ld a, [wItemQuantityChange]
	ld [wItemQuantityChange], a ; What is the point of this operation?
	scf

.done
	call CloseWindow
	ret

.MenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 6, 9, SCREEN_WIDTH - 1, 12
	dw NULL
	db -1 ; default option
	db 0

.PlaceApricornName:
	call MenuBoxCoord2Tile
	ld de, SCREEN_WIDTH + 1
	add hl, de
	ld d, h
	ld e, l
	farcall PlaceMenuItemName
	ret

PlaceApricornQuantity:
	call MenuBoxCoord2Tile
	ld de, 2 * SCREEN_WIDTH + 10
	add hl, de
	ld [hl], '×'
	inc hl
	ld de, wItemQuantityChange
	lb bc, PRINTNUM_LEADINGZEROS | 1, 2
	jp PrintNum

Kurt_GetQuantityOfApricorn:
	farcall GetApricornQuantity
	ld a, [wItemQuantityChange]
	and a
	ret

Kurt_GiveUpSelectedQuantityOfSelectedApricorn:
	ld hl, wNumItems
	call TossItem
	ret
