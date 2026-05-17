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

DEF PACK_ITEM_ICON_FIRST_TILE EQU $60
DEF PACK_ITEM_ICON_TILES EQU 9

Pack:
	ld hl, wOptions
	set NO_TEXT_SCROLL, [hl]
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
	ld a, [wPackJumptableIndex]
	ld [wJumptableIndex], a
	call Pack_InitColors
	ret

.InitItemsPocket:
	xor a ; ITEM_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.ItemsPocketMenu:
	ld hl, ItemsPocketMenuHeader
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
	ld b, PACKSTATE_INITMEDICINEPOCKET ; left
	ld c, PACKSTATE_INITBALLSPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call .ItemBallsKey_LoadSubmenu
	ret

.InitKeyItemsPocket:
	ld a, KEY_ITEM_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.KeyItemsPocketMenu:
	ld hl, KeyItemsPocketMenuHeader
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
	ld b, PACKSTATE_INITBALLSPOCKET ; left
	ld c, PACKSTATE_INITBERRIESPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call .ItemBallsKey_LoadSubmenu
	ret

.InitBerriesPocket:
	ld a, BERRY_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.BerriesPocketMenu:
	ld hl, BerriesPocketMenuHeader
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
	ld b, PACKSTATE_INITKEYITEMSPOCKET ; left
	ld c, PACKSTATE_INITMEDICINEPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call .ItemBallsKey_LoadSubmenu
	ret

.InitBallsPocket:
	ld a, BALL_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.BallsPocketMenu:
	ld hl, BallsPocketMenuHeader
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
	ld b, PACKSTATE_INITITEMSPOCKET ; left
	ld c, PACKSTATE_INITKEYITEMSPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call .ItemBallsKey_LoadSubmenu
	ret

.InitMedicinePocket:
	ld a, MEDICINE_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.MedicinePocketMenu:
	ld hl, MedicinePocketMenuHeader
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
	ld b, PACKSTATE_INITBERRIESPOCKET ; left
	ld c, PACKSTATE_INITITEMSPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call .ItemBallsKey_LoadSubmenu
	ret

.ItemBallsKey_LoadSubmenu:
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
	push de
	call LoadMenuHeader
	call VerticalMenu
	call ExitMenu
	pop hl
	ret c
	ld a, [wMenuCursorY]
	dec a
	call Pack_GetJumptablePointer
	jp hl

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
	call WaitBGMap_DrawPackGFX
	call Pack_InitColors
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
	farcall SelectQuantityToToss
	push af
	call ExitMenu
	pop af
	jr c, .finish
	call Pack_GetItemName
	ld hl, AskQuantityThrowAwayText
	call MenuTextbox
	call YesNoBox
	push af
	call ExitMenu
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
	call TryGiveItemToPartymon
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
	call WaitBGMap_DrawPackGFX
	call Pack_InitColors
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
	ld a, [wPackJumptableIndex]
	ld [wJumptableIndex], a
	call Pack_InitColors
	ret

.InitItemsPocket:
	xor a ; ITEM_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.ItemsPocketMenu:
	ld hl, ItemsPocketMenuHeader
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
	ld b, PACKSTATE_INITMEDICINEPOCKET ; left
	ld c, PACKSTATE_INITBALLSPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call ItemSubmenu
	ret

.InitKeyItemsPocket:
	ld a, KEY_ITEM_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.KeyItemsPocketMenu:
	ld hl, KeyItemsPocketMenuHeader
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
	ld b, PACKSTATE_INITBALLSPOCKET ; left
	ld c, PACKSTATE_INITBERRIESPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call ItemSubmenu
	ret

.InitBerriesPocket:
	ld a, BERRY_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.BerriesPocketMenu:
	ld hl, BerriesPocketMenuHeader
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
	ld b, PACKSTATE_INITKEYITEMSPOCKET ; left
	ld c, PACKSTATE_INITMEDICINEPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call ItemSubmenu
	ret

.InitBallsPocket:
	ld a, BALL_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.BallsPocketMenu:
	ld hl, BallsPocketMenuHeader
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
	ld b, PACKSTATE_INITITEMSPOCKET ; left
	ld c, PACKSTATE_INITKEYITEMSPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call ItemSubmenu
	ret

.InitMedicinePocket:
	ld a, MEDICINE_POCKET
	ld [wCurPocket], a
	call ClearPocketList
	call DrawPocketName
	call WaitBGMap_DrawPackGFX
	call Pack_JumptableNext
	ret

.MedicinePocketMenu:
	ld hl, MedicinePocketMenuHeader
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
	ld b, PACKSTATE_INITBERRIESPOCKET ; left
	ld c, PACKSTATE_INITITEMSPOCKET ; right
	call Pack_InterpretJoypad
	ret c
	call ItemSubmenu
	ret

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
	push de
	call LoadMenuHeader
	call VerticalMenu
	call ExitMenu
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
	call WaitBGMap_DrawPackGFX
	call Pack_InitColors
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
	ret

DepositSellInitPackBuffers:
	xor a
	ldh [hBGMapMode], a
	ld [wJumptableIndex], a ; PACKSTATE_INITGFX
	ld [wPackJumptableIndex], a ; PACKSTATE_INITGFX
	ld [wCurPocket], a ; ITEM_POCKET
	ld [wPackUsedItem], a
	ld [wSwitchItem], a
	call Pack_InitGFX
	call Pack_InitColors
	ret

DepositSellPack:
.loop
	call .RunJumptable
	call DepositSellTutorial_InterpretJoypad
	jr c, .loop
	ret

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

DepositSellTutorial_InterpretJoypad:
	ld hl, wMenuJoypad
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
	scf
	ret

.a_button
	ld a, TRUE
	ld [wPackUsedItem], a
	and a
	ret

.b_button
	xor a ; FALSE
	ld [wPackUsedItem], a
	and a
	ret

.d_left
	ld a, [wJumptableIndex]
	dec a
	cp -1
	jr nz, .left_ok
	ld a, NUM_POCKETS - 1
.left_ok
	ld [wJumptableIndex], a
	push de
	ld de, SFX_SWITCH_POCKETS
	call PlaySFX
	pop de
	scf
	ret

.d_right
	ld a, [wJumptableIndex]
	inc a
	cp NUM_POCKETS
	jr nz, .right_ok
	xor a
.right_ok
	ld [wJumptableIndex], a
	push de
	ld de, SFX_SWITCH_POCKETS
	call PlaySFX
	pop de
	scf
	ret

TutorialPack:
	call DepositSellInitPackBuffers
	ld a, [wInputType]
	or a
	jr z, .loop
	farcall _DudeAutoInput_RightA
.loop
	call .RunJumptable
	call DepositSellTutorial_InterpretJoypad
	jr c, .loop
	xor a ; FALSE
	ld [wPackUsedItem], a
	ret

.RunJumptable:
	ld a, [wJumptableIndex]
	ld hl, .dw
	call Pack_GetJumptablePointer
	jp hl

.dw
; entries correspond to *_POCKET constants
	dw .Items
	dw .Balls
	dw .KeyItems
	dw .Berries
	dw .Medicine

.Items:
	xor a ; ITEM_POCKET
	ld hl, .ItemsMenuHeader
	jp .DisplayPocket

.ItemsMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .ItemsMenuData
	db 1 ; default option

.ItemsMenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wDudeNumItems
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

.KeyItems:
	ld a, KEY_ITEM_POCKET
	ld hl, .KeyItemsMenuHeader
	jp .DisplayPocket

.KeyItemsMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .KeyItemsMenuData
	db 1 ; default option

.KeyItemsMenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_NORMAL ; item format
	dbw 0, wDudeNumKeyItems
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

.Berries:
	ld a, BERRY_POCKET
	ld hl, .BerriesMenuHeader
	jp .DisplayPocket

.BerriesMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .BerriesMenuData
	db 1 ; default option

.BerriesMenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wDudeNumBerries
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

.Balls:
	ld a, BALL_POCKET
	ld hl, .BallsMenuHeader
	jp .DisplayPocket

.BallsMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .BallsMenuData
	db 1 ; default option

.BallsMenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wDudeNumBalls
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

.Medicine:
	ld a, MEDICINE_POCKET
	ld hl, .MedicineMenuHeader
	jp .DisplayPocket

.MedicineMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 7, 1, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MedicineMenuData
	db 1 ; default option

.MedicineMenuData:
	db STATICMENU_ENABLE_SELECT | STATICMENU_ENABLE_LEFT_RIGHT | STATICMENU_ENABLE_START | STATICMENU_WRAP | STATICMENU_CURSOR ; flags
	db 5, 8 ; rows, columns
	db SCROLLINGMENU_ITEMS_QUANTITY ; item format
	dbw 0, wDudeNumMedicine
	dba PlaceMenuItemName
	dba PlaceMenuItemQuantity
	dba UpdatePackItemDescription

.DisplayPocket:
	push hl
	call InitPocket
	pop hl
	call CopyMenuHeader
	call ScrollingMenu
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

Pack_PrintTextNoScroll:
	ld a, [wOptions]
	push af
	set NO_TEXT_SCROLL, a
	ld [wOptions], a
	call PrintText
	pop af
	ld [wOptions], a
	ret

WaitBGMap_DrawPackGFX:
	call WaitBGMap
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
	ld hl, vTiles2 tile $50
	lb bc, BANK(PackGFX), 15
	call Request2bpp
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
	call MenuTextbox
	call YesNoBox
	push af
	call ExitMenu
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
	call ClearBGPalettes
	call ClearTilemap
	call ClearSprites
	call DisableLCD
	ld hl, PackMenuGFX
	ld de, vTiles2
	ld bc, $60 tiles
	ld a, BANK(PackMenuGFX)
	call FarCopyBytes
; Background (blue if male, pink if female)
	hlcoord 0, 1
	ld bc, 11 * SCREEN_WIDTH
	ld a, $24
	call ByteFill
; This is where the items themselves will be listed.
	hlcoord 5, 1
	lb bc, 11, 15
	call ClearBox
; ◀▶ POCKET       ▼▲ ITEMS
	hlcoord 0, 0
	ld a, $28
	ld c, SCREEN_WIDTH
.loop
	ld [hli], a
	inc a
	dec c
	jr nz, .loop
	call DrawPocketName
	call PlacePackGFX
; Place the textbox for displaying the item description
	hlcoord 0, SCREEN_HEIGHT - 4 - 2
	lb bc, 4, SCREEN_WIDTH - 2
	call Textbox
	call Pack_LoadColors
	call EnableLCD
	call DrawPackGFX
	ret

PlacePackGFX:
	hlcoord 0, 1
	ld a, $50
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
	ld a, [wCurPocket]
	; * 15
	ld d, a
	swap a
	sub d
	ld d, 0
	ld e, a
	ld hl, .tilemap
	add hl, de
	ld d, h
	ld e, l
	hlcoord 0, 5
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

.tilemap: ; 5x15
; the 5x3 pieces correspond to *_POCKET constants
INCBIN "gfx/pack/pack_menu.tilemap"
; MEDICINE_POCKET
	db $00, $04, $04, $04, $01 ; top border
	db $1a, $1b, $1c, $1d, $1e ; Medicine
	db $02, $05, $05, $05, $03 ; bottom border

UpdatePackItemIcon:
	ld a, [wMenuSelection]
	cp -1
	jr z, ShowPackItemEmptyIcon
	call PlacePackItemIcon
	ld a, [wMenuSelection]
	call GetPackItemIcon
	jr LoadPackItemIcon

GetPackItemIcon:
	ld b, a
	ld hl, PackItemIconTable
.loop
	ld a, [hli]
	cp -1
	jr z, .question_icon
	cp b
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
	ret

.question_icon
	ld de, PackItemQuestionIconGFX
	ld hl, PackItemQuestionIconPalette
	ret

ShowPackItemEmptyIcon:
	call PlacePackItemIcon
	ld de, PackItemEmptyIconGFX
	ld hl, PackItemEmptyIconPalette
	jr LoadPackItemIcon

LoadPackItemIcon:
	push hl
	ld hl, vTiles2 tile PACK_ITEM_ICON_FIRST_TILE
	lb bc, BANK(PackItemQuestionIconGFX), PACK_ITEM_ICON_TILES
	call Request2bpp
	pop hl
	call LoadPackItemIconPalette
	ret

LoadPackItemIconPalette:
	ldh a, [hCGB]
	and a
	ret z
	ld de, wBGPals1 palette 6
	ld bc, 1 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
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
	call WaitBGMap
	call Pack_LoadColors
	call DelayFrame
	ret

Pack_LoadColors:
	ld b, SCGB_PACKPALS
	call GetSGBLayout
	call SetDefaultBGPAndOBP
	ret

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

PackMenuGFX:
INCBIN "gfx/pack/pack_menu.2bpp"
PackGFX:
INCBIN "gfx/pack/pack.2bpp"

PackItemQuestionIconGFX:
INCBIN "gfx/items/misc/placeholder.2bpp"
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
PackItemBrightPowderIconGFX:
INCBIN "gfx/items/general/bright_powder.2bpp"
PackItemEscapeRopeIconGFX:
INCBIN "gfx/items/general/escape_rope.2bpp"
PackItemFireStoneIconGFX:
INCBIN "gfx/items/general/fire_stone.2bpp"
PackItemExpShareIconGFX:
INCBIN "gfx/items/general/exp_share.2bpp"
PackItemTinyMushroomIconGFX:
INCBIN "gfx/items/general/tinymushroom.2bpp"
PackItemBigMushroomIconGFX:
INCBIN "gfx/items/general/big_mushroom.2bpp"
PackItemBlackBeltIconGFX:
INCBIN "gfx/items/general/black_belt.2bpp"
PackItemBlackGlassesIconGFX:
INCBIN "gfx/items/general/black_glasses.2bpp"
PackItemPearlIconGFX:
INCBIN "gfx/items/general/pearl.2bpp"
PackItemBigPearlIconGFX:
INCBIN "gfx/items/general/big_pearl.2bpp"
PackItemEverstoneIconGFX:
INCBIN "gfx/items/general/everstone.2bpp"
PackItemFocusBandIconGFX:
INCBIN "gfx/items/general/focus_band.2bpp"
PackItemHardStoneIconGFX:
INCBIN "gfx/items/general/hard_stone.2bpp"
PackItemCharcoalIconGFX:
INCBIN "gfx/items/general/charcoal.2bpp"
PackItemDragonFangIconGFX:
INCBIN "gfx/items/general/dragon_fang.2bpp"
PackItemDragonScaleIconGFX:
INCBIN "gfx/items/general/dragon_scale.2bpp"
PackItemBicycleIconGFX:
INCBIN "gfx/items/key_items/bicycle.2bpp"
PackItemCoinCaseIconGFX:
INCBIN "gfx/items/key_items/coin_case.2bpp"
PackItemGoodRodIconGFX:
INCBIN "gfx/items/key_items/good_rod.2bpp"
PackItemCardKeyIconGFX:
INCBIN "gfx/items/key_items/card_key.2bpp"
PackItemApricornIconGFX:
INCBIN "gfx/items/apricorns/red_apricorn.2bpp"
