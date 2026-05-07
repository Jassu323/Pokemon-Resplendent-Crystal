; Move detail icon constants
DEF MOVE_MENU_TYPE_ICON_TILE EQU $68 ; uses $68-$6f
DEF MOVE_MENU_TYPE_ICON_ATTR EQU $0e ; VRAM bank 1, BG palette 6
DEF MOVE_MENU_CATEGORY_ICON_TILE EQU $70 ; uses $70-$77
DEF MOVE_MENU_CATEGORY_ICON_ATTR EQU $0f ; VRAM bank 1, BG palette 7

; Move detail icon positions
DEF MOVE_MENU_TYPE_ICON_X     EQU 11
DEF MOVE_MENU_CATEGORY_ICON_X EQU 15
DEF MOVE_MENU_ICON_Y          EQU 12

MoveCategoryIconGFXPointers:
	table_width 3
	dba PhysicalMoveCategoryIconGFX
	dba SpecialMoveCategoryIconGFX
	dba StatusMoveCategoryIconGFX
	assert_table_length NUM_MOVE_CATEGORIES

HasNoItems:
	ld a, [wNumItems]
	and a
	ret nz
	ld a, [wNumKeyItems]
	and a
	ret nz
	ld a, [wNumBalls]
	and a
	ret nz
	ld hl, wTMsHMs
	ld b, NUM_TMS + NUM_HMS
.loop
	ld a, [hli]
	and a
	jr nz, .done
	dec b
	jr nz, .loop
	scf
	ret
.done
	and a
	ret

TossItemFromPC:
	push de
	call PartyMonItemName
	farcall _CheckTossableItem
	ld a, [wItemAttributeValue]
	and a
	jr nz, .key_item
	ld hl, .ItemsTossOutHowManyText
	call MenuTextbox
	farcall SelectQuantityToToss
	push af
	call CloseWindow
	call ExitMenu
	pop af
	jr c, .quit
	ld hl, .ItemsThrowAwayText
	call MenuTextbox
	call YesNoBox
	push af
	call ExitMenu
	pop af
	jr c, .quit
	pop hl
	ld a, [wCurItemQuantity]
	call TossItem
	call PartyMonItemName
	ld hl, .ItemsDiscardedText
	call MenuTextbox
	call ExitMenu
	and a
	ret

.key_item
	call .CantToss
.quit
	pop hl
	scf
	ret

.ItemsTossOutHowManyText:
	text_far _ItemsTossOutHowManyText
	text_end

.ItemsThrowAwayText:
	text_far _ItemsThrowAwayText
	text_end

.ItemsDiscardedText:
	text_far _ItemsDiscardedText
	text_end

.CantToss:
	ld hl, .ItemsTooImportantText
	call MenuTextboxBackup
	ret

.ItemsTooImportantText:
	text_far _ItemsTooImportantText
	text_end

CantUseItem:
	ld hl, ItemsOakWarningText
	call MenuTextboxWaitButton
	ret

ItemsOakWarningText:
	text_far _ItemsOakWarningText
	text_end

PartyMonItemName:
	ld a, [wCurItem]
	ld [wNamedObjectIndex], a
	call GetItemName
	call CopyName1
	ret

CancelPokemonAction:
	farcall InitPartyMenuWithCancel
	farcall UnfreezeMonIcons
	ld a, 1
	ret

PokemonActionSubmenu:
	hlcoord 1, 15
	lb bc, 2, 18
	call ClearBox
	farcall MonSubmenu
	call GetCurNickname
	ld a, [wMenuSelection]
	ld hl, .Actions
	ld de, 3
	call IsInArray
	jr nc, .nothing

	inc hl
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jp hl

.nothing
	ld a, 0
	ret

.Actions:
	dbw MONMENUITEM_CUT,        MonMenu_Cut
	dbw MONMENUITEM_FLY,        MonMenu_Fly
	dbw MONMENUITEM_SURF,       MonMenu_Surf
	dbw MONMENUITEM_STRENGTH,   MonMenu_Strength
	dbw MONMENUITEM_FLASH,      MonMenu_Flash
	dbw MONMENUITEM_WHIRLPOOL,  MonMenu_Whirlpool
	dbw MONMENUITEM_DIG,        MonMenu_Dig
	dbw MONMENUITEM_TELEPORT,   MonMenu_Teleport
	dbw MONMENUITEM_SOFTBOILED, MonMenu_Softboiled_MilkDrink
	dbw MONMENUITEM_MILKDRINK,  MonMenu_Softboiled_MilkDrink
	dbw MONMENUITEM_HEADBUTT,   MonMenu_Headbutt
	dbw MONMENUITEM_WATERFALL,  MonMenu_Waterfall
	dbw MONMENUITEM_ROCKSMASH,  MonMenu_RockSmash
	dbw MONMENUITEM_SWEETSCENT, MonMenu_SweetScent
	dbw MONMENUITEM_STATS,      OpenPartyStats
	dbw MONMENUITEM_SWITCH,     SwitchPartyMons
	dbw MONMENUITEM_ITEM,       GiveTakePartyMonItem
	dbw MONMENUITEM_CANCEL,     CancelPokemonAction
	dbw MONMENUITEM_MOVE,       ManagePokemonMoves
	dbw MONMENUITEM_MAIL,       MonMailAction

SwitchPartyMons:
; Don't try if there's nothing to switch!
	ld a, [wPartyCount]
	cp 2
	jr c, .DontSwitch

	ld a, [wCurPartyMon]
	inc a
	ld [wSwitchMon], a

	farcall HoldSwitchmonIcon
	farcall InitPartyMenuNoCancel

	ld a, PARTYMENUACTION_MOVE
	ld [wPartyMenuActionText], a
	farcall WritePartyMenuTilemap
	farcall PlacePartyMenuText

	hlcoord 0, 1
	ld bc, SCREEN_WIDTH * 2
	ld a, [wSwitchMon]
	dec a
	call AddNTimes
	ld [hl], '▷'
	call WaitBGMap
	call SetDefaultBGPAndOBP
	call DelayFrame

	farcall PartyMenuSelect
	bit B_PAD_B, b
	jr c, .DontSwitch

	farcall _SwitchPartyMons

	xor a
	ld [wPartyMenuActionText], a

	farcall LoadPartyMenuGFX
	farcall InitPartyMenuWithCancel
	farcall InitPartyMenuGFX

	ld a, 1
	ret

.DontSwitch:
	xor a
	ld [wPartyMenuActionText], a
	call CancelPokemonAction
	ret

GiveTakePartyMonItem:
; Eggs can't hold items!
	ld a, [wCurPartySpecies]
	cp EGG
	jr z, .cancel

	ld hl, GiveTakeItemMenuData
	call LoadMenuHeader
	call VerticalMenu
	call ExitMenu
	jr c, .cancel

	call GetCurNickname
	ld hl, wStringBuffer1
	ld de, wMonOrItemNameBuffer
	ld bc, MON_NAME_LENGTH
	call CopyBytes
	ld a, [wMenuCursorY]
	cp 1
	jr nz, .take

	call LoadStandardMenuHeader
	call ClearPalettes
	call .GiveItem
	call ClearPalettes
	call LoadFontsBattleExtra
	call ExitMenu
	ld a, 0
	ret

.take
	call TakePartyItem
	ld a, 3
	ret

.cancel
	ld a, 3
	ret

.GiveItem:
	farcall DepositSellInitPackBuffers

.loop
	farcall DepositSellPack

	ld a, [wPackUsedItem]
	and a
	jr z, .quit

	ld a, [wCurPocket]
	cp KEY_ITEM_POCKET
	jr z, .next

	call CheckTossableItem
	ld a, [wItemAttributeValue]
	and a
	jr nz, .next

	call TryGiveItemToPartymon
	jr .quit

.next
	ld hl, ItemCantHeldText
	call MenuTextboxBackup
	jr .loop

.quit
	ret

TryGiveItemToPartymon:
	call SpeechTextbox
	call PartyMonItemName
	call GetPartyItemLocation
	ld a, [hl]
	and a
	jr z, .give_item_to_mon

	push hl
	ld d, a
	farcall ItemIsMail
	pop hl
	jr c, .please_remove_mail
	ld a, [hl]
	jr .already_holding_item

.give_item_to_mon
	call GiveItemToPokemon
	ld hl, PokemonHoldItemText
	call MenuTextboxBackup
	call GivePartyItem
	ret

.please_remove_mail
	ld hl, PokemonRemoveMailText
	call MenuTextboxBackup
	ret

.already_holding_item
	ld [wNamedObjectIndex], a
	call GetItemName
	ld hl, PokemonAskSwapItemText
	call StartMenuYesNo
	jr c, .abort

	call GiveItemToPokemon
	ld a, [wNamedObjectIndex]
	push af
	ld a, [wCurItem]
	ld [wNamedObjectIndex], a
	pop af
	ld [wCurItem], a
	call ReceiveItemFromPokemon
	jr nc, .bag_full

	ld hl, PokemonSwapItemText
	call MenuTextboxBackup
	ld a, [wNamedObjectIndex]
	ld [wCurItem], a
	call GivePartyItem
	ret

.bag_full
	ld a, [wNamedObjectIndex]
	ld [wCurItem], a
	call ReceiveItemFromPokemon
	ld hl, ItemStorageFullText
	call MenuTextboxBackup

.abort
	ret

GivePartyItem:
	call GetPartyItemLocation
	ld a, [wCurItem]
	ld [hl], a
	ld d, a
	farcall ItemIsMail
	jr nc, .done
	call ComposeMailMessage

.done
	ret

TakePartyItem:
	call SpeechTextbox
	call GetPartyItemLocation
	ld a, [hl]
	and a
	jr z, .not_holding_item

	ld [wCurItem], a
	call ReceiveItemFromPokemon
	jr nc, .item_storage_full

	farcall ItemIsMail
	call GetPartyItemLocation
	ld a, [hl]
	ld [wNamedObjectIndex], a
	ld [hl], NO_ITEM
	call GetItemName
	ld hl, PokemonTookItemText
	call MenuTextboxBackup
	jr .done

.not_holding_item
	ld hl, PokemonNotHoldingText
	call MenuTextboxBackup
	jr .done

.item_storage_full
	ld hl, ItemStorageFullText
	call MenuTextboxBackup

.done
	ret

GiveTakeItemMenuData:
	db MENU_SPRITE_ANIMS | MENU_BACKUP_TILES ; flags
	menu_coords 12, 12, SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1
	dw .Items
	db 1 ; default option

.Items:
	db STATICMENU_CURSOR ; flags
	db 2 ; # items
	db "GIVE@"
	db "TAKE@"

PokemonSwapItemText:
	text_far _PokemonSwapItemText
	text_end

PokemonHoldItemText:
	text_far _PokemonHoldItemText
	text_end

PokemonRemoveMailText:
	text_far _PokemonRemoveMailText
	text_end

PokemonNotHoldingText:
	text_far _PokemonNotHoldingText
	text_end

ItemStorageFullText:
	text_far _ItemStorageFullText
	text_end

PokemonTookItemText:
	text_far _PokemonTookItemText
	text_end

PokemonAskSwapItemText:
	text_far _PokemonAskSwapItemText
	text_end

ItemCantHeldText:
	text_far _ItemCantHeldText
	text_end

GetPartyItemLocation:
	push af
	ld a, MON_ITEM
	call GetPartyParamLocation
	pop af
	ret

ReceiveItemFromPokemon:
	ld a, 1
	ld [wItemQuantityChange], a
	ld hl, wNumItems
	jp ReceiveItem

GiveItemToPokemon:
	ld a, 1
	ld [wItemQuantityChange], a
	ld hl, wNumItems
	jp TossItem

StartMenuYesNo:
	call MenuTextbox
	call YesNoBox
	jp ExitMenu

ComposeMailMessage:
	ld de, wTempMailMessage
	farcall _ComposeMailMessage
	ld hl, wPlayerName
	ld de, wTempMailAuthor
	ld bc, NAME_LENGTH - 1
	call CopyBytes
	ld hl, wPlayerID
	ld bc, 2
	call CopyBytes
	ld a, [wCurPartySpecies]
	ld [de], a
	inc de
	ld a, [wCurItem]
	ld [de], a
	ld a, [wCurPartyMon]
	ld hl, sPartyMail
	ld bc, MAIL_STRUCT_LENGTH
	call AddNTimes
	ld d, h
	ld e, l
	ld hl, wTempMail
	ld bc, MAIL_STRUCT_LENGTH
	ld a, BANK(sPartyMail)
	call OpenSRAM
	call CopyBytes
	call CloseSRAM
	ret

MonMailAction:
; If in the time capsule or trade center,
; selecting the mail only allows you to
; read the mail.
	ld a, [wLinkMode]
	cp LINK_TIMECAPSULE
	jr z, .read
	cp LINK_TRADECENTER
	jr z, .read

; Show the READ/TAKE/QUIT menu.
	ld hl, .MenuHeader
	call LoadMenuHeader
	call VerticalMenu
	call ExitMenu

; Interpret the menu.
	jp c, .done
	ld a, [wMenuCursorY]
	cp $1
	jr z, .read
	cp $2
	jr z, .take
	jp .done

.read
	farcall ReadPartyMonMail
	ld a, $0
	ret

.take
	ld hl, .MailAskSendToPCText
	call StartMenuYesNo
	jr c, .RemoveMailToBag
	ld a, [wCurPartyMon]
	ld b, a
	farcall SendMailToPC
	jr c, .MailboxFull
	ld hl, .MailSentToPCText
	call MenuTextboxBackup
	jr .done

.MailboxFull:
	ld hl, .MailboxFullText
	call MenuTextboxBackup
	jr .done

.RemoveMailToBag:
	ld hl, .MailLoseMessageText
	call StartMenuYesNo
	jr c, .done
	call GetPartyItemLocation
	ld a, [hl]
	ld [wCurItem], a
	call ReceiveItemFromPokemon
	jr nc, .BagIsFull
	call GetPartyItemLocation
	ld [hl], $0
	call GetCurNickname
	ld hl, .MailDetachedText
	call MenuTextboxBackup
	jr .done

.BagIsFull:
	ld hl, .MailNoSpaceText
	call MenuTextboxBackup
	jr .done

.done
	ld a, $3
	ret

.MenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 12, 10, SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR ; flags
	db 3 ; items
	db "READ@"
	db "TAKE@"
	db "QUIT@"

.MailLoseMessageText:
	text_far _MailLoseMessageText
	text_end

.MailDetachedText:
	text_far _MailDetachedText
	text_end

.MailNoSpaceText:
	text_far _MailNoSpaceText
	text_end

.MailAskSendToPCText:
	text_far _MailAskSendToPCText
	text_end

.MailboxFullText:
	text_far _MailboxFullText
	text_end

.MailSentToPCText:
	text_far _MailSentToPCText
	text_end

OpenPartyStats:
	call LoadStandardMenuHeader
	call ClearSprites
; PartyMon
	xor a
	ld [wMonType], a
	call LowVolume
	predef StatsScreenInit
	call MaxVolume
	call ExitMenu
	ld a, 0
	ret

MonMenu_Cut:
	farcall CutFunction
	ld a, [wFieldMoveSucceeded]
	cp $1
	jr nz, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_Fly:
	farcall FlyFunction
	ld a, [wFieldMoveSucceeded]
	cp $2
	jr z, .Fail
	cp $0
	jr z, .Error
	farcall StubbedTrainerRankings_Fly
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

.Error:
	ld a, $0
	ret

.NoReload: ; unreferenced
	ld a, $1
	ret

MonMenu_Flash:
	farcall FlashFunction
	ld a, [wFieldMoveSucceeded]
	cp $1
	jr nz, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_Strength:
	farcall StrengthFunction
	ld a, [wFieldMoveSucceeded]
	cp $1
	jr nz, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_Whirlpool:
	farcall WhirlpoolFunction
	ld a, [wFieldMoveSucceeded]
	cp $1
	jr nz, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_Waterfall:
	farcall WaterfallFunction
	ld a, [wFieldMoveSucceeded]
	cp $1
	jr nz, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_Teleport:
	farcall TeleportFunction
	ld a, [wFieldMoveSucceeded]
	and a
	jr z, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_Surf:
	farcall SurfFunction
	ld a, [wFieldMoveSucceeded]
	and a
	jr z, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_Dig:
	farcall DigFunction
	ld a, [wFieldMoveSucceeded]
	cp $1
	jr nz, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_Softboiled_MilkDrink:
	call .CheckMonHasEnoughHP
	jr nc, .NotEnoughHP
	farcall Softboiled_MilkDrinkFunction
	jr .finish

.NotEnoughHP:
	ld hl, .PokemonNotEnoughHPText
	call PrintText

.finish
	xor a
	ld [wPartyMenuActionText], a
	ld a, $3
	ret

.PokemonNotEnoughHPText:
	text_far _PokemonNotEnoughHPText
	text_end

.CheckMonHasEnoughHP:
; Need to have at least (MaxHP / 5) HP left.
	ld a, MON_MAXHP
	call GetPartyParamLocation
	ld a, [hli]
	ldh [hDividend + 0], a
	ld a, [hl]
	ldh [hDividend + 1], a
	ld a, 5
	ldh [hDivisor], a
	ld b, 2
	call Divide
	ld a, MON_HP + 1
	call GetPartyParamLocation
	ldh a, [hQuotient + 3]
	sub [hl]
	dec hl
	ldh a, [hQuotient + 2]
	sbc [hl]
	ret

MonMenu_Headbutt:
	farcall HeadbuttFunction
	ld a, [wFieldMoveSucceeded]
	cp $1
	jr nz, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_RockSmash:
	farcall RockSmashFunction
	ld a, [wFieldMoveSucceeded]
	cp $1
	jr nz, .Fail
	ld b, $4
	ld a, $2
	ret

.Fail:
	ld a, $3
	ret

MonMenu_SweetScent:
	farcall SweetScentFromMenu
	ld b, $4
	ld a, $2
	ret

ChooseMoveToDelete:
	ld hl, wOptions
	ld a, [hl]
	push af
	set NO_TEXT_SCROLL, [hl]
	call LoadFontsBattleExtra
	call .ChooseMoveToDelete
	pop bc
	ld a, b
	ld [wOptions], a
	push af
	call ClearBGPalettes
	pop af
	ret

.ChooseMoveToDelete
	call SetUpMoveScreenBG
	ld de, DeleteMoveScreen2DMenuData
	call Load2DMenuData
	call SetUpMoveList
	ld hl, w2DMenuFlags1
	set _2DMENU_ENABLE_SPRITE_ANIMS_F, [hl]
	jr .enter_loop

.loop
	call ScrollingMenuJoypad
	bit B_PAD_B, a
	jp nz, .b_button
	bit B_PAD_A, a
	jp nz, .a_button

.enter_loop
	call PrepareToPlaceMoveData
	call PlaceMoveData
	jp .loop

.a_button
	and a
	jr .finish

.b_button
	scf

.finish
	push af
	xor a
	ld [wSwitchMon], a
	ld hl, w2DMenuFlags1
	res _2DMENU_ENABLE_SPRITE_ANIMS_F, [hl]
	call ClearSprites
	call ClearTilemap
	pop af
	ret

DeleteMoveScreen2DMenuData:
	db 3, 1 ; cursor start y, x
	db 3, 1 ; rows, columns
	db _2DMENU_ENABLE_SPRITE_ANIMS ; flags 1
	db 0 ; flags 2
	dn 2, 0 ; cursor offset
	db PAD_UP | PAD_DOWN | PAD_A | PAD_B ; accepted buttons

ManagePokemonMoves:
	ld a, [wCurPartySpecies]
	cp EGG
	jr z, .egg
	ld hl, wOptions
	ld a, [hl]
	push af
	set NO_TEXT_SCROLL, [hl]
	call MoveScreenLoop
	pop af
	ld [wOptions], a
	call ClearBGPalettes

.egg
	ld a, $0
	ret

MoveScreenLoop:
	ld a, [wCurPartyMon]
	inc a
	ld [wPartyMenuCursor], a
	call SetUpMoveScreenBG
	call PlaceMoveScreenArrows
	ld de, MoveScreen2DMenuData
	call Load2DMenuData
.loop
	call SetUpMoveList
	ld hl, w2DMenuFlags1
	set _2DMENU_ENABLE_SPRITE_ANIMS_F, [hl]
	jr .skip_joy

.joy_loop
	call ScrollingMenuJoypad
	bit B_PAD_B, a
	jp nz, .b_button
	bit B_PAD_A, a
	jp nz, .a_button
	bit B_PAD_RIGHT, a
	jp nz, .d_right
	bit B_PAD_LEFT, a
	jp nz, .d_left

.skip_joy
	call PrepareToPlaceMoveData
	ld a, [wSwappingMove]
	and a
	jr nz, .moving_move
	call PlaceMoveData
	jp .joy_loop

.moving_move
	ld a, ' '
	hlcoord 1, 11
	ld bc, 5
	call ByteFill
	hlcoord 1, 11
	lb bc, 5, 7
	call ClearBox
	hlcoord 1, 12
	lb bc, 5, SCREEN_WIDTH - 2
	call ClearBox
	hlcoord 2, 13
	ld de, String_MoveWhere
	call PlaceString
	jp .joy_loop
.b_button
	call PlayClickSFX
	call WaitSFX
	ld a, [wSwappingMove]
	and a
	jp z, .exit

	ld a, [wSwappingMove]
	ld [wMenuCursorY], a
	xor a
	ld [wSwappingMove], a
	hlcoord 1, 2
	lb bc, 8, SCREEN_WIDTH - 2
	call ClearBox
	jp .loop

.d_right
	ld a, [wSwappingMove]
	and a
	jp nz, .joy_loop

	ld a, [wCurPartyMon]
	ld b, a
	push bc
	call .cycle_right
	pop bc
	ld a, [wCurPartyMon]
	cp b
	jp z, .joy_loop
	ld de, SFX_SWITCH_POCKETS
	call PlaySFX
	jp MoveScreenLoop

.d_left
	ld a, [wSwappingMove]
	and a
	jp nz, .joy_loop
	ld a, [wCurPartyMon]
	ld b, a
	push bc
	call .cycle_left
	pop bc
	ld a, [wCurPartyMon]
	cp b
	jp z, .joy_loop
	ld de, SFX_SWITCH_POCKETS
	call PlaySFX
	jp MoveScreenLoop

.cycle_right
	ld a, [wCurPartyMon]
	inc a
	ld [wCurPartyMon], a
	ld c, a
	ld b, 0
	ld hl, wPartySpecies
	add hl, bc
	ld a, [hl]
	cp -1
	jr z, .cycle_left
	cp EGG
	ret nz
	jr .cycle_right

.cycle_left
	ld a, [wCurPartyMon]
	and a
	ret z
.cycle_left_loop
	ld a, [wCurPartyMon]
	dec a
	ld [wCurPartyMon], a
	ld c, a
	ld b, 0
	ld hl, wPartySpecies
	add hl, bc
	ld a, [hl]
	cp EGG
	ret nz
	ld a, [wCurPartyMon]
	and a
	jr z, .cycle_right
	jr .cycle_left_loop

.a_button
	call PlayClickSFX
	call WaitSFX
	ld a, [wSwappingMove]
	and a
	jr nz, .place_move
	ld a, [wMenuCursorY]
	ld [wSwappingMove], a
	call PlaceHollowCursor
	jp .moving_move

.place_move
	ld hl, wPartyMon1Moves
	ld bc, PARTYMON_STRUCT_LENGTH
	ld a, [wCurPartyMon]
	call AddNTimes
	push hl
	call .copy_move
	pop hl
	ld bc, wPartyMon1PP - wPartyMon1Moves
	add hl, bc
	call .copy_move
	ld a, [wBattleMode]
	jr z, .swap_moves
	ld hl, wBattleMonMoves
	ld bc, wBattleMonStructEnd - wBattleMon
	ld a, [wCurPartyMon]
	call AddNTimes
	push hl
	call .copy_move
	pop hl
	ld bc, wBattleMonPP - wBattleMonMoves
	add hl, bc
	call .copy_move

.swap_moves
	ld de, SFX_SWITCH_POKEMON
	call PlaySFX
	call WaitSFX
	ld de, SFX_SWITCH_POKEMON
	call PlaySFX
	call WaitSFX
	hlcoord 1, 2
	lb bc, 8, 18
	call ClearBox
	hlcoord 10, 10
	lb bc, 1, 9
	call ClearBox
	jp .loop

.copy_move
	push hl
	ld a, [wMenuCursorY]
	dec a
	ld c, a
	ld b, 0
	add hl, bc
	ld d, h
	ld e, l
	pop hl
	ld a, [wSwappingMove]
	dec a
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [de]
	ld b, [hl]
	ld [hl], a
	ld a, b
	ld [de], a
	ret

.exit
	xor a
	ld [wSwappingMove], a
	ld hl, w2DMenuFlags1
	res _2DMENU_ENABLE_SPRITE_ANIMS_F, [hl]
	call ClearSprites
	jp ClearTilemap

MoveScreen2DMenuData:
	db 3, 1 ; cursor start y, x
	db 3, 1 ; rows, columns
	db _2DMENU_ENABLE_SPRITE_ANIMS ; flags 1
	db 0 ; flags 2
	dn 2, 0 ; cursor offsets
	db PAD_CTRL_PAD | PAD_A | PAD_B ; accepted buttons

String_MoveWhere:
	db "Select a move<NEXT>to swap places.@"

SetUpMoveScreenBG:
	call ClearBGPalettes
	call ClearTilemap
	call ClearSprites
	xor a
	ldh [hBGMapMode], a
	farcall LoadStatsScreenPageTilesGFX
	farcall ClearSpriteAnims2
	ld a, [wCurPartyMon]
	ld e, a
	ld d, 0
	ld hl, wPartySpecies
	add hl, de
	ld a, [hl]
	ld [wTempIconSpecies], a
	ld e, MONICON_MOVES
	farcall LoadMenuMonIcon
	hlcoord 0, -1
	ld b, 1
	ld c, 18
	call Textbox
	hlcoord 0, 11
	ld b, 5
	ld c, 18
	call Textbox
	hlcoord 2, 0
	lb bc, 2, 3
	call ClearBox
	xor a
	ld [wMonType], a
	ld hl, wPartyMonNicknames
	ld a, [wCurPartyMon]
	call GetNickname
	hlcoord 5, 1
	call PlaceString
	push bc
	farcall CopyMonToTempMon
	pop hl
	call PrintLevel
	ld hl, wPlayerHPPal
	call SetHPPal
	ld b, SCGB_MOVE_LIST
	call GetSGBLayout

	hlcoord 16, 0
	lb bc, 1, 3
	call ClearBox

	ldh a, [hCGB]
	and a
	ret z

	call MoveMenu_SetMoveTypeIconAttrs
	call MoveMenu_SetMoveCategoryIconAttrs
	farcall ApplyAttrmap
	ret

SetUpMoveList:
	xor a
	ldh [hBGMapMode], a
	ld [wSwappingMove], a
	ld [wMonType], a
	predef CopyMonToTempMon
	ld hl, wTempMonMoves
	ld de, wListMoves_MoveIndicesBuffer
	ld bc, NUM_MOVES
	call CopyBytes
	ld a, SCREEN_WIDTH * 2
	ld [wListMovesLineSpacing], a
	hlcoord 2, 3
	predef ListMoves
	hlcoord 10, 4
	predef ListMovePP
	call WaitBGMap
	call SetDefaultBGPAndOBP
	ld a, [wNumMoves]
	inc a
	ld [w2DMenuNumRows], a
	hlcoord 0, 11
	ld b, 5
	ld c, 18
	jp Textbox

PrepareToPlaceMoveData:
	ld hl, wPartyMon1Moves
	ld bc, PARTYMON_STRUCT_LENGTH
	ld a, [wCurPartyMon]
	call AddNTimes
	ld a, [wMenuCursorY]
	dec a
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [hl]
	ld [wCurSpecies], a
	hlcoord 1, 12
	lb bc, 5, 18
	jp ClearBox

PlaceMoveData:
	xor a
	ldh [hBGMapMode], a
	
; Print UI elements
	hlcoord 0, 10
	ld de, String_MoveType_Top
	call PlaceString
	hlcoord 0, 11
	ld de, String_MoveType_Bottom
	call PlaceString
	hlcoord 1, 11
	ld de, String_MoveAtk
	call PlaceString
	hlcoord 1, 12
	ld de, String_MoveAcc
	call PlaceString
	hlcoord 1, 13
	ld de, String_MoveEff
	call PlaceString
	
; Print move accuracy
	ld a, [wCurSpecies]
	ld l, a
	ld a, MOVE_ACC
	call GetMoveAttribute
	call ConvertPercentages
	ld [wBuffer1], a
	ld de, wBuffer1
	lb bc, 1, 3
	hlcoord 5, 12
	call PrintNum

; Print move effect chance
	ld a, [wCurSpecies]
	ld l, a
	ld a, MOVE_CHANCE
	call GetMoveAttribute
	cp 1
	jr c, .if_null_chance
	call ConvertPercentages
	ld [wBuffer1], a
	ld de, wBuffer1
	lb bc, 1, 3
	hlcoord 5, 13
	call PrintNum
	jr .skip_null_chance

.if_null_chance
	ld de, String_MoveNoPower
	ld bc, 3
	hlcoord 5, 13
	call PlaceString

.skip_null_chance
	
; Print move power
	ld a, [wCurSpecies]
	ld l, a
	ld a, MOVE_POWER
	call GetMoveAttribute
	hlcoord 5, 11
	cp 2
	jr c, .no_power
	ld [wTextDecimalByte], a
	ld de, wTextDecimalByte
	lb bc, 1, 3
	call PrintNum
	jr .description

.no_power
	ld de, String_MoveNoPower
	call PlaceString

; Print move description
.description
	hlcoord 1, 15
	predef PrintMoveDescription

; Print move type icon
	call MoveMenu_LoadMoveTypeIconGFX
	hlcoord MOVE_MENU_TYPE_ICON_X, MOVE_MENU_ICON_Y
	ld a, MOVE_MENU_TYPE_ICON_TILE
	call MoveMenu_Draw4x2Icon

; Print move category icon
	call MoveMenu_LoadMoveCategoryIcon
	hlcoord MOVE_MENU_CATEGORY_ICON_X, MOVE_MENU_ICON_Y
	ld a, MOVE_MENU_CATEGORY_ICON_TILE
	call MoveMenu_Draw4x2Icon

	ld a, $1
	ldh [hBGMapMode], a
	ret
	
; This converts values out of 256 into a value
; out of 100.
ConvertPercentages:
	ldh [hMultiplicand + 2], a
	xor a
	ldh [hMultiplicand + 1], a
	ldh [hMultiplicand], a
	ld a, 100
	ldh [hMultiplier], a ; 1 byte only
	call Multiply
	ldh a, [hProduct + 2]
    and a ; check if our result is zero
    ret z ; if zero, done
    inc a ; else, add one
    ret

MoveMenu_LoadMoveTypeIconGFX:
; Queue selected move's type icon graphics and load its palette.

	farcall StatsScreen_LoadCurrentMoveTypeIconGFX_Bank1
	farcall LoadMoveMenuCurrentTypeIconPalette
	ret

MoveMenu_LoadMoveCategoryIcon:
	call MoveMenu_LoadMoveCategoryIconGFX
	farcall LoadMoveMenuCurrentCategoryIconPalette
	ret


MoveMenu_Draw4x2Icon:
; Draw one 4x2 icon at hl.
; input:
;   hl = tilemap destination
;   a  = starting tile ID

	ld c, 4
.top
	ld [hli], a
	inc a
	dec c
	jr nz, .top

	ld de, SCREEN_WIDTH - 4
	add hl, de

	ld c, 4
.bottom
	ld [hli], a
	inc a
	dec c
	jr nz, .bottom
	ret

MoveMenu_SetMoveTypeIconAttrs:
	ldh a, [hCGB]
	and a
	ret z

	hlcoord MOVE_MENU_TYPE_ICON_X, MOVE_MENU_ICON_Y, wAttrmap
	ld a, MOVE_MENU_TYPE_ICON_ATTR
	call MoveMenu_Set4x2IconAttrs
	ret


MoveMenu_Set4x2IconAttrs:
; Set attrs for one 4x2 icon at hl.
; input:
;   hl = attrmap destination
;   a  = attr byte

	push bc
	push de

	ld c, 4
.top
	ld [hli], a
	dec c
	jr nz, .top

	ld de, SCREEN_WIDTH - 4
	add hl, de

	ld c, 4
.bottom
	ld [hli], a
	dec c
	jr nz, .bottom

	pop de
	pop bc
	ret

MoveMenu_GetCurrentMoveCategory:
; Return selected move's category in a.
; Uses wCurSpecies as selected move ID.
;
; returns:
;   MOVE_CATEGORY_PHYSICAL
;   MOVE_CATEGORY_SPECIAL
;   MOVE_CATEGORY_STATUS

	ld a, [wCurSpecies]
	ld l, a
	ld a, MOVE_POWER
	call GetMoveAttribute
	cp 2
	jr c, .status

	ld a, [wCurSpecies]
	ld l, a
	ld a, MOVE_TYPE
	call GetMoveAttribute
	cp SPECIAL
	jr nc, .special

.physical
	ld a, MOVE_CATEGORY_PHYSICAL
	ret

.special
	ld a, MOVE_CATEGORY_SPECIAL
	ret

.status
	ld a, MOVE_CATEGORY_STATUS
	ret

MoveMenu_LoadMoveCategoryIconGFX:
; Load selected move's category icon graphics into VRAM bank 1.

	call MoveMenu_GetCurrentMoveCategory

	; de = a * 3, because MoveCategoryIconGFXPointers entries are dba: bank + word
	ld e, a
	ld d, 0
	ld hl, MoveCategoryIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	; b = bank, de = source pointer
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	ld hl, vTiles2 tile MOVE_MENU_CATEGORY_ICON_TILE

	ldh a, [rVBK]
	push af
	ld a, $1
	ldh [rVBK], a

	ld c, 8
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

MoveMenu_SetMoveCategoryIconAttrs:
	ldh a, [hCGB]
	and a
	ret z

	hlcoord MOVE_MENU_CATEGORY_ICON_X, MOVE_MENU_ICON_Y, wAttrmap
	ld a, MOVE_MENU_CATEGORY_ICON_ATTR
	call MoveMenu_Set4x2IconAttrs
	ret


; UI elements
String_MoveType_Top:
	db "┌───────┐@"
String_MoveType_Bottom:
	db "│       └@"
String_MoveAtk:
	db "POW/@"
String_MoveAcc:
	db "ACC/@"
String_MoveEff:
	db "EFF/@"
String_MoveNoPower:
	db "---@"

PlaceMoveScreenArrows:
	call PlaceMoveScreenLeftArrow
	call PlaceMoveScreenRightArrow
	ret

PlaceMoveScreenLeftArrow:
	ld a, [wCurPartyMon]
	and a
	ret z
	ld c, a
	ld e, a
	ld d, 0
	ld hl, wPartyCount
	add hl, de
.loop
	ld a, [hl]
	and a
	jr z, .prev
	cp MON_TABLE_ENTRIES + 1
	jr c, .legal

.prev
	dec hl
	dec c
	jr nz, .loop
	ret

.legal
	hlcoord 16, 0
	ld [hl], '◀'
	ret

PlaceMoveScreenRightArrow:
	ld a, [wCurPartyMon]
	inc a
	ld c, a
	ld a, [wPartyCount]
	cp c
	ret z
	ld e, c
	ld d, 0
	ld hl, wPartySpecies
	add hl, de
.loop
	ld a, [hl]
	cp -1
	ret z
	and a
	jr z, .next
	cp MON_TABLE_ENTRIES + 1
	jr c, .legal

.next
	inc hl
	jr .loop

.legal
	hlcoord 18, 0
	ld [hl], '▶'
	ret
