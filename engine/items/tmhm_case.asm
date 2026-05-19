DEF TMHM_CASE_STATIC_TILE EQU $00
DEF TMHM_CASE_BORDER_TILE EQU $24
DEF TMHM_CASE_ITEMS_TILE  EQU $40
DEF TMHM_CASE_SELECT_TILE EQU $45
DEF TMHM_CASE_STATS_TILE  EQU $48
DEF TMHM_CASE_PAGE_TILE   EQU $60
DEF TMHM_CASE_PAGE_1_TILE EQU TMHM_CASE_PAGE_TILE + 4
DEF TMHM_CASE_PAGE_SLASH_TILE EQU TMHM_CASE_PAGE_TILE + 12
DEF TMHM_CASE_TITLE_TILE  EQU $6d
DEF TMHM_CASE_HEADER_TILE EQU $5e
DEF TMHM_CASE_POWER_TILE  EQU $50
DEF TMHM_CASE_ACCURACY_TILE EQU TMHM_CASE_POWER_TILE + 2
DEF TMHM_CASE_EFFECT_CHANCE_TILE EQU TMHM_CASE_ACCURACY_TILE + 2
DEF TMHM_CASE_ANIM_TILE   EQU $00

DEF TMHM_CASE_PAGE_LENGTH EQU 8
DEF TMHM_CASE_PAGE_WIDTH  EQU 4
DEF TMHM_CASE_PAGE_COUNT  EQU 8
DEF TMHM_CASE_ANIM_FRAME_TILES EQU 9
DEF TMHM_CASE_ANIM_FRAME_COUNT EQU 4
DEF TMHM_CASE_ANIM_OAM_COUNT   EQU 9
DEF TMHM_CASE_TYPE_ICON_TILE EQU TMHM_CASE_ANIM_TILE + TMHM_CASE_ANIM_FRAME_TILES * TMHM_CASE_ANIM_FRAME_COUNT
DEF TMHM_CASE_TYPE_ICON_TILES EQU 4
DEF TMHM_CASE_CATEGORY_ICON_TILE EQU TMHM_CASE_TYPE_ICON_TILE + TMHM_CASE_TYPE_ICON_TILES
DEF TMHM_CASE_CATEGORY_ICON_TILES EQU 2 * NUM_MOVE_CATEGORIES
DEF TMHM_CASE_PARTY_ICON_TILE EQU TMHM_CASE_CATEGORY_ICON_TILE + TMHM_CASE_CATEGORY_ICON_TILES
DEF TMHM_CASE_PARTY_ICON_TILES EQU 8
DEF TMHM_CASE_PARTY_ICON_OAM_COUNT EQU PARTY_LENGTH * 4
DEF TMHM_CASE_PARTY_ICON_PALETTE EQU 2
DEF TMHM_CASE_MOVE_INFO_ICON_OAM_COUNT EQU 6
DEF TMHM_CASE_PAGE_DISC_PALETTE_COUNT EQU 7

DEF TMHM_CASE_TYPE_ICON_X EQU 8 * 8 + 8
DEF TMHM_CASE_TYPE_ICON_Y EQU 9 * 8 + 15
DEF TMHM_CASE_CATEGORY_ICON_X EQU 12 * 8 + 8
DEF TMHM_CASE_CATEGORY_ICON_Y EQU 9 * 8 + 15

DEF TMHM_CASE_GREEN_DARK_R  EQU 02
DEF TMHM_CASE_GREEN_DARK_G  EQU 26
DEF TMHM_CASE_GREEN_DARK_B  EQU 00
DEF TMHM_CASE_GREEN_LIGHT_R EQU 10
DEF TMHM_CASE_GREEN_LIGHT_G EQU 31
DEF TMHM_CASE_GREEN_LIGHT_B EQU 08

TMHMCase:
	ld a, $1
	ldh [hInMenu], a
	ld a, BANK(wTMsHMs)
	ldh [rWBK], a
	xor a
	ld [wMenuCursorPosition], a
	ld [wMenuScrollPosition], a
	ld [wMenuScrollPosition + 1], a
	ld [wMenuScrollPosition + 2], a
	ld [wMenuScrollPosition + 3], a
	call TMHMCase_InitGFX
	call TMHMCase_UpdateSelection_NoApply
	call TMHMCase_TransferTilemapAndAttrmap
	call TMHMCase_LoadColors
	call TMHMCase_LoadCurrentMoveInfoIconPalettes

.loop
	call TMHMCase_UpdateAnimatedDiscOAM
	call TMHMCase_PlacePartyIconOAM
	call DelayFrame
	call TMHMCase_AdvanceAnimTimer
	call JoyTextDelay
	ldh a, [hJoyPressed]
	bit B_PAD_A, a
	jr nz, .a_button
	bit B_PAD_B, a
	jr nz, .quit
	bit B_PAD_SELECT, a
	jr nz, .select
	ldh a, [hJoyLast]
	bit B_PAD_LEFT, a
	jr nz, .left
	bit B_PAD_RIGHT, a
	jr nz, .right
	bit B_PAD_UP, a
	jr nz, .up
	bit B_PAD_DOWN, a
	jr nz, .down
	jr .loop

.left
	call TMHMCase_MoveLeft
	jr .loop

.right
	call TMHMCase_MoveRight
	jr .loop

.up
	call TMHMCase_MoveUp
	jr .loop

.down
	call TMHMCase_MoveDown
	jr .loop

.select
	call TMHMCase_ToggleStats
	jr .loop

.a_button
	call TMHMCase_ItemMenu
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
	xor a
	ldh [hInMenu], a
	ret

TMHMCase_MoveLeft:
	ld a, [wMenuCursorPosition]
	and TMHM_CASE_PAGE_WIDTH - 1
	jr z, .previous_page
	ld a, [wMenuCursorPosition]
	dec a
	jp TMHMCase_TryMoveToSlot

	.previous_page
	call TMHMCase_StoreCurrentPageSlotCount
	call TMHMCase_PreviousPage
	call TMHMCase_PlayPageSFX
	ld a, [wMenuCursorPosition]
	add TMHM_CASE_PAGE_WIDTH - 1
	ld d, a
	call TMHMCase_FindValidSlotBackward
	jp TMHMCase_SetPageCursorAndUpdate

TMHMCase_MoveRight:
	ld a, [wMenuCursorPosition]
	and TMHM_CASE_PAGE_WIDTH - 1
	cp TMHM_CASE_PAGE_WIDTH - 1
	jr z, .next_page_from_edge
	ld a, [wMenuCursorPosition]
	inc a
	ld d, a
	call TMHMCase_IsSlotValid
	ld a, d
	jp c, TMHMCase_SetCursorAndUpdate
	ld a, [wMenuCursorPosition]
	and TMHM_CASE_PAGE_WIDTH
	jr .next_page

.next_page_from_edge
	ld a, [wMenuCursorPosition]
	and TMHM_CASE_PAGE_WIDTH

	.next_page
	push af
	call TMHMCase_StoreCurrentPageSlotCount
	call TMHMCase_NextPage
	call TMHMCase_PlayPageSFX
	pop af
	ld d, a
	call TMHMCase_FindValidSlotForward
	jp TMHMCase_SetPageCursorAndUpdate

TMHMCase_MoveUp:
	ld a, [wMenuCursorPosition]
	cp TMHM_CASE_PAGE_WIDTH
	ret c
	sub TMHM_CASE_PAGE_WIDTH
	jp TMHMCase_TryMoveToSlot

TMHMCase_MoveDown:
	ld a, [wMenuCursorPosition]
	add TMHM_CASE_PAGE_WIDTH
	cp TMHM_CASE_PAGE_LENGTH
	ret nc
	jp TMHMCase_TryMoveToSlot

TMHMCase_TryMoveToSlot:
	ld d, a
	call TMHMCase_IsSlotValid
	ret nc
	ld a, d
	jp TMHMCase_SetCursorAndUpdate

TMHMCase_SetCursorAndUpdate:
	ld b, a
	ld a, [wMenuCursorPosition]
	ld c, a
	ld a, b
	ld [wMenuCursorPosition], a
	xor a
	ld [wMenuScrollPosition + 1], a
	ld a, c
	call TMHMCase_BufferDiscBGAtSlot
	call TMHMCase_DrawTMHMIcons
	jp TMHMCase_UpdateSelectionAndTransfer

TMHMCase_SetPageCursorAndUpdate:
	ld b, a
	ld a, [wMenuCursorPosition]
	push af
	ld a, b
	ld [wMenuCursorPosition], a
	xor a
	ld [wMenuScrollPosition + 1], a
	call TMHMCase_LoadPageDiscPalettes_NoApply
	pop af
	call TMHMCase_DrawPageTransitionIcons
	call TMHMCase_DrawPageIndicator
	jp TMHMCase_UpdatePageSelectionAndTransfer

TMHMCase_NextPage:
	ld a, [wMenuScrollPosition]
	inc a
	cp TMHM_CASE_PAGE_COUNT
	jr c, .store
	xor a

.store
	ld [wMenuScrollPosition], a
	ret

TMHMCase_PreviousPage:
	ld a, [wMenuScrollPosition]
	and a
	jr z, .last
	dec a
	jr .store

.last
	ld a, TMHM_CASE_PAGE_COUNT - 1

.store
	ld [wMenuScrollPosition], a
	ret

TMHMCase_PlayPageSFX:
	ld de, SFX_SWITCH_POCKETS
	jp PlaySFX

TMHMCase_ToggleStats:
	ld a, PAD_SELECT
	call MenuClickSound
	ld hl, wMenuScrollPosition + 2
	ld a, [hl]
	xor 1
	ld [hl], a
	jp TMHMCase_UpdateSelectionAndTransfer

TMHMCase_ItemMenu:
	call TMHMCase_GetSelectedTMHMNumber
	jr nc, .wrong
	call TMHMCase_IsCurrentTMHMOwned
	jr nc, .wrong
	ld a, [wMenuCursorPosition]
	push af
	ld a, [wMenuScrollPosition]
	push af
	ld a, [wMenuScrollPosition + 2]
	push af
	call TMHMCase_SetSelectedTMHMItem
	ld a, PAD_A
	call MenuClickSound
	call TMHMCase_HideUseMenuPartyIconOAM
	ld hl, TMHMCaseUseMenuHeader
	call LoadMenuHeader
	call VerticalMenu
	push af
	ld a, [wMenuCursorY]
	ld b, a
	push bc
	call ExitMenu
	pop bc
	pop af
	jr c, .quit_menu
	ld a, b
	dec a
	jr nz, .quit_menu
	call TMHMCase_TransferTilemapAndAttrmap
	call TMHMCase_RestoreUseMenuCategoryOAM
	call TMHMCase_PlacePartyIconOAM
	call TMHMCase_UseSelectedTMHM
	pop af
	ld [wMenuScrollPosition + 2], a
	pop af
	ld [wMenuScrollPosition], a
	pop af
	ld [wMenuCursorPosition], a
	jp TMHMCase_Redraw

.quit_menu
	pop af
	ld [wMenuScrollPosition + 2], a
	pop af
	ld [wMenuScrollPosition], a
	pop af
	ld [wMenuCursorPosition], a
	call TMHMCase_TransferTilemapAndAttrmap
	call TMHMCase_RestoreUseMenuCategoryOAM
	jp TMHMCase_PlacePartyIconOAM

.wrong
	ld de, SFX_WRONG
	jp PlaySFX

TMHMCase_SetSelectedTMHMItem:
	ld a, [wTempTMHM]
	add TM01 - 1
	ld [wCurItem], a
	ld a, [wTempTMHM]
	dec a
	ld c, a
	ld b, 0
	ld hl, wTMsHMs
	add hl, bc
	ld a, [hl]
	ld [wItemQuantity], a
	ld [wCurItemQuantity], a
	ret

TMHMCase_UseSelectedTMHM:
	call TMHMCase_GetPartyCount
	and a
	jr z, .no_pokemon
	call TMHMCase_AskTeachTMHM
	ret c
	farcall ChooseMonToLearnTMHM
	ret c
	farcall TeachTMHM
	ret

.no_pokemon
	ld hl, TMHMCaseYouDontHaveAMonText
	jp TMHMCase_PrintTextNoScroll

TMHMCase_AskTeachTMHM:
	ld hl, wOptions
	ld a, [hl]
	push af
	res NO_TEXT_SCROLL, [hl]
	call TMHMCase_SetPutativeTMHMMove
	ld a, [wPutativeTMHMMove]
	ld [wNamedObjectIndex], a
	call GetMoveName
	call CopyName1
	ld hl, TMHMCaseBootedTMText
	ld a, [wCurItem]
	cp HM01
	jr c, .tm
	ld hl, TMHMCaseBootedHMText

.tm
	call PrintText
	ld hl, TMHMCaseContainedMoveText
	call PrintText
	call TMHMCase_HideUseMenuPartyIconOAM
	call YesNoBox
	push af
	call TMHMCase_RestoreUseMenuCategoryOAM
	call TMHMCase_PlacePartyIconOAM
	pop af
	pop bc
	ld a, b
	ld [wOptions], a
	ret

TMHMCase_PrintTextNoScroll:
	ld a, [wOptions]
	push af
	set NO_TEXT_SCROLL, a
	ld [wOptions], a
	call PrintText
	pop af
	ld [wOptions], a
	ret

TMHMCase_Redraw:
	call TMHMCase_InitGFX
	call TMHMCase_UpdateSelection_NoApply
	call TMHMCase_TransferTilemapAndAttrmap
	call TMHMCase_LoadColors
	jp TMHMCase_LoadCurrentMoveInfoIconPalettes

TMHMCase_FindValidSlotForward:
	ld a, d

.loop
	cp TMHM_CASE_PAGE_LENGTH
	jr nc, .first
	ld d, a
	call TMHMCase_IsSlotValid
	ld a, d
	ret c
	inc a
	jr .loop

.first
	xor a
	ret

TMHMCase_FindValidSlotBackward:
	ld a, d

.loop
	ld d, a
	call TMHMCase_IsSlotValid
	ld a, d
	ret c
	and a
	jr z, .last
	dec a
	jr .loop

.last
	ld a, TMHM_CASE_PAGE_LENGTH - 1

.last_loop
	ld d, a
	call TMHMCase_IsSlotValid
	ld a, d
	ret c
	dec a
	jr .last_loop

TMHMCase_StoreCurrentPageSlotCount:
	ld a, [wMenuScrollPosition]
	call TMHMCase_GetPageSlotCount
	ld [wMenuScrollPosition + 3], a
	ret

TMHMCase_GetCurrentPageSlotCount:
	ld a, [wMenuScrollPosition]
	; fallthrough

TMHMCase_GetPageSlotCount:
	cp 6
	jr c, .full_page
	jr z, .tm49_50
	ld a, NUM_HMS
	ret

.tm49_50
	ld a, 2
	ret

.full_page
	ld a, TMHM_CASE_PAGE_LENGTH
	ret

TMHMCase_IsSlotValid:
	ld e, a
	cp TMHM_CASE_PAGE_LENGTH
	ret nc
	ld a, [wMenuScrollPosition]
	cp 6
	jr c, .valid
	jr z, .tm49_50
	ld a, e
	cp NUM_HMS
	jr c, .valid
	and a
	ret

.tm49_50
	ld a, e
	cp 2
	jr c, .valid
	and a
	ret

.valid
	scf
	ret

TMHMCase_GetSelectedTMHMNumber:
	ld a, [wMenuCursorPosition]
	jr TMHMCase_GetSlotTMHMNumber

TMHMCase_GetSlotTMHMNumber:
	ld d, a
	call TMHMCase_IsSlotValid
	ret nc
	ld a, [wMenuScrollPosition]
	cp 6
	jr c, .tm_page
	jr z, .tm49_50
	ld a, d
	add NUM_TMS + 1
	ld [wTempTMHM], a
	scf
	ret

.tm49_50
	ld a, d
	add NUM_TMS - 1
	ld [wTempTMHM], a
	scf
	ret

.tm_page
	add a
	add a
	add a
	ld b, a
	ld a, d
	add b
	inc a
	ld [wTempTMHM], a
	scf
	ret

TMHMCase_GetPageDiscPaletteTable:
	ldh a, [rWBK]
	push af
	ld a, BANK(wStringBuffer4)
	ldh [rWBK], a
	ld hl, wStringBuffer4
	pop af
	ldh [rWBK], a
	ret

TMHMCase_GetPageDiscPalette:
	push af
	call TMHMCase_GetPageDiscPaletteTable
	pop af
	ld e, a
	ldh a, [rWBK]
	push af
	ld a, BANK(wStringBuffer4)
	ldh [rWBK], a
	ld c, 1
	ld b, TMHM_CASE_PAGE_DISC_PALETTE_COUNT

.loop
	ld a, [hli]
	cp e
	jr z, .found
	inc c
	dec b
	jr nz, .loop
	pop af
	ldh [rWBK], a
	xor a
	ret

.found
	ld a, c
	ld b, a
	pop af
	ldh [rWBK], a
	ld a, b
	ret

TMHMCase_GetUnownedDiscPalette:
	ldh a, [rWBK]
	push af
	ld a, BANK(wStringBuffer4)
	ldh [rWBK], a
	ld hl, wStringBuffer4
	ld c, 1
	ld b, TMHM_CASE_PAGE_DISC_PALETTE_COUNT

.loop
	ld a, [hli]
	cp $ff
	jr z, .found
	inc c
	dec b
	jr nz, .loop
	pop af
	ldh [rWBK], a
	xor a
	ret

.found
	ld a, c
	ld b, a
	pop af
	ldh [rWBK], a
	ld a, b
	ret

TMHMCase_BuildPageDiscPaletteMap:
	ldh a, [rWBK]
	push af
	ld a, BANK(wStringBuffer4)
	ldh [rWBK], a
	ld hl, wStringBuffer4
	ld bc, TMHM_CASE_PAGE_DISC_PALETTE_COUNT
	ld a, $ff
	call ByteFill
	xor a
	ld [wBuffer1], a
	call TMHMCase_PageHasUnownedDisc
	jr nc, .scan
	ld a, 1
	ld [wBuffer1], a

.scan
	xor a

.loop
	cp TMHM_CASE_PAGE_LENGTH
	jr nc, .done
	push af
	call TMHMCase_GetSlotTMHMNumber
	jr nc, .next
	call TMHMCase_IsCurrentTMHMOwned
	jr nc, .next
	call TMHMCase_GetSelectedMoveTypeCategory
	jr nc, .next
	ld a, b
	call TMHMCase_RegisterPageDiscPalette

.next
	pop af
	inc a
	jr .loop

.done
	pop af
	ldh [rWBK], a
	ret

TMHMCase_PageHasUnownedDisc:
	xor a

.loop
	cp TMHM_CASE_PAGE_LENGTH
	jr nc, .none
	push af
	call TMHMCase_GetSlotTMHMNumber
	jr nc, .next
	call TMHMCase_IsCurrentTMHMOwned
	jr nc, .found

.next
	pop af
	inc a
	jr .loop

.found
	pop af
	scf
	ret

.none
	and a
	ret

TMHMCase_RegisterPageDiscPalette:
	ld e, a
	ld a, [wBuffer1]
	ld c, a
	ld b, 0
	ld hl, wStringBuffer4
	add hl, bc
	ld a, TMHM_CASE_PAGE_DISC_PALETTE_COUNT
	sub c
	ld b, a

.find
	ld a, [hli]
	cp e
	ret z
	dec b
	jr nz, .find
	ld a, [wBuffer1]
	ld c, a
	ld b, 0
	ld hl, wStringBuffer4
	add hl, bc
	ld a, TMHM_CASE_PAGE_DISC_PALETTE_COUNT
	sub c
	ld b, a

.find_empty
	ld a, [hl]
	cp $ff
	jr z, .store
	inc hl
	dec b
	jr nz, .find_empty
	ret

.store
	ld [hl], e
	ret

TMHMCase_UpdateSelectionAndTransfer:
	call TMHMCase_UpdateSelection
	jp TMHMCase_TransferTilemapAndAttrmap

TMHMCase_UpdatePageSelectionAndTransfer:
	call TMHMCase_UpdateSelection_NoApply
	xor a
	ldh [hCGBPalUpdate], a
	call TMHMCase_TransferTilemapAndAttrmap
	jp TMHMCase_ApplyMoveInfoIconPalettes

TMHMCase_TransferTilemapAndAttrmap:
	call HDMATransferTilemapAndAttrmap_Menu
	xor a
	ldh [hBGMapMode], a
	ret

TMHMCase_InitGFX:
	xor a
	ldh [hBGMapMode], a
	call ClearBGPalettes
	call ClearSprites
	call DisableLCD
	call ClearTilemap
	call TMHMCase_ClearAttrmap
	call TMHMCase_LoadGFX
	call TMHMCase_LoadPartyIconGFX
	call TMHMCase_BuildPageDiscPaletteMap
	call TMHMCase_DrawLayout
	call TMHMCase_PlacePartyIconOAM
	call EnableLCD
	ret

TMHMCase_ClearAttrmap:
	hlcoord 0, 0, wAttrmap
	ld bc, wAttrmapEnd - wAttrmap
	xor a
	jp ByteFill

TMHMCase_LoadGFX:
	ld hl, PackMenuGFX
	ld de, vTiles2
	ld bc, $60 tiles
	ld a, BANK(PackMenuGFX)
	call FarCopyBytes

	ld hl, TMHMCaseAnimGFX
	ld de, vTiles0 tile TMHM_CASE_ANIM_TILE
	ld bc, TMHM_CASE_ANIM_FRAME_TILES * TMHM_CASE_ANIM_FRAME_COUNT tiles
	ld a, BANK(TMHMCaseAnimGFX)
	call FarCopyBytes

	ld hl, TMHMCaseCategoryIconGFX
	ld de, vTiles0 tile TMHM_CASE_CATEGORY_ICON_TILE
	ld bc, TMHM_CASE_CATEGORY_ICON_TILES tiles
	ld a, BANK(TMHMCaseCategoryIconGFX)
	call FarCopyBytes

	ld hl, TMHMCaseStaticGFX
	ld de, vTiles2 tile TMHM_CASE_STATIC_TILE
	ld bc, 9 tiles
	ld a, BANK(TMHMCaseStaticGFX)
	call FarCopyBytes

	ld hl, TMHMCaseTitleGFX
	ld de, vTiles2 tile TMHM_CASE_TITLE_TILE
	ld bc, 12 tiles
	ld a, BANK(TMHMCaseTitleGFX)
	call FarCopyBytes

	ld hl, TMHMCaseHeaderGFX
	ld de, vTiles2 tile TMHM_CASE_HEADER_TILE
	ld bc, 1 tiles
	ld a, BANK(TMHMCaseHeaderGFX)
	call FarCopyBytes

	ld hl, TMHMCasePowerIconGFX
	ld de, vTiles2 tile TMHM_CASE_POWER_TILE
	ld bc, 2 tiles
	ld a, BANK(TMHMCasePowerIconGFX)
	call FarCopyBytes

	ld hl, TMHMCaseAccuracyIconGFX
	ld de, vTiles2 tile TMHM_CASE_ACCURACY_TILE
	ld bc, 2 tiles
	ld a, BANK(TMHMCaseAccuracyIconGFX)
	call FarCopyBytes

	ld hl, TMHMCaseEffectChanceIconGFX
	ld de, vTiles2 tile TMHM_CASE_EFFECT_CHANCE_TILE
	ld bc, 2 tiles
	ld a, BANK(TMHMCaseEffectChanceIconGFX)
	call FarCopyBytes
	jp TMHMCase_LoadPageGFX

TMHMCase_LoadPageGFX:
	ld de, FontInversed + ($0f * TILE_1BPP_SIZE) ; P
	ld hl, vTiles2 tile TMHM_CASE_PAGE_TILE
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($20 * TILE_1BPP_SIZE) ; a
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_TILE + 1)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($26 * TILE_1BPP_SIZE) ; g
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_TILE + 2)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($24 * TILE_1BPP_SIZE) ; e
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_TILE + 3)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($77 * TILE_1BPP_SIZE) ; 1
	ld hl, vTiles2 tile TMHM_CASE_PAGE_1_TILE
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($78 * TILE_1BPP_SIZE) ; 2
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_1_TILE + 1)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($79 * TILE_1BPP_SIZE) ; 3
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_1_TILE + 2)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($7a * TILE_1BPP_SIZE) ; 4
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_1_TILE + 3)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($7b * TILE_1BPP_SIZE) ; 5
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_1_TILE + 4)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($7c * TILE_1BPP_SIZE) ; 6
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_1_TILE + 5)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($7d * TILE_1BPP_SIZE) ; 7
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_1_TILE + 6)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($7e * TILE_1BPP_SIZE) ; 8
	ld hl, vTiles2 tile (TMHM_CASE_PAGE_1_TILE + 7)
	lb bc, BANK(FontInversed), 1
	call Get1bpp
	ld de, FontInversed + ($73 * TILE_1BPP_SIZE) ; /
	ld hl, vTiles2 tile TMHM_CASE_PAGE_SLASH_TILE
	lb bc, BANK(FontInversed), 1
	jp Get1bpp

TMHMCase_DrawLayout:
	hlcoord 0, 0
	lb bc, 2, SCREEN_WIDTH
	ld a, TMHM_CASE_HEADER_TILE
	call FillBoxWithByte

	hlcoord 0, 2
	lb bc, 10, 2
	ld a, TMHM_CASE_BORDER_TILE
	call FillBoxWithByte
	hlcoord 18, 2
	lb bc, 10, 2
	ld a, TMHM_CASE_BORDER_TILE
	call FillBoxWithByte

	hlcoord 0, 2, wAttrmap
	lb bc, 10, 2
	xor a
	call FillBoxWithByte
	hlcoord 18, 2, wAttrmap
	lb bc, 10, 2
	xor a
	call FillBoxWithByte

	hlcoord 7, 0
	lb bc, 2, 6
	ld a, TMHM_CASE_TITLE_TILE
	call TMHMCase_PlaceTileBlock

	hlcoord 17, 0
	ld a, TMHM_CASE_SELECT_TILE
	ld c, 3
	call TMHMCase_PlaceHeaderRow

	hlcoord 17, 1
	ld a, TMHM_CASE_STATS_TILE
	ld c, 3
	call TMHMCase_PlaceHeaderRow

	call TMHMCase_DrawPageIndicator
	call TMHMCase_DrawTMHMIcons
	jp TMHMCase_DrawTextboxes

TMHMCase_PlaceHeaderRow:
	ld [hli], a
	inc a
	dec c
	jr nz, TMHMCase_PlaceHeaderRow
	ret

TMHMCase_DrawPageIndicator:
	hlcoord 0, 0
	ld a, TMHM_CASE_PAGE_TILE
	ld [hli], a
	inc a
	ld [hli], a
	inc a
	ld [hli], a
	inc a
	ld [hl], a

	hlcoord 1, 1
	ld a, [wMenuScrollPosition]
	add TMHM_CASE_PAGE_1_TILE
	ld [hli], a
	ld a, TMHM_CASE_PAGE_SLASH_TILE
	ld [hli], a
	ld a, TMHM_CASE_PAGE_1_TILE + TMHM_CASE_PAGE_COUNT - 1
	ld [hl], a
	ret

TMHMCase_DrawTMHMIcons:
	xor a
	call TMHMCase_DrawTMHMSlot
	ld a, 1
	call TMHMCase_DrawTMHMSlot
	ld a, 2
	call TMHMCase_DrawTMHMSlot
	ld a, 3
	call TMHMCase_DrawTMHMSlot
	ld a, 4
	call TMHMCase_DrawTMHMSlot
	ld a, 5
	call TMHMCase_DrawTMHMSlot
	ld a, 6
	call TMHMCase_DrawTMHMSlot
	ld a, 7
	jp TMHMCase_DrawTMHMSlot

TMHMCase_DrawPageTransitionIcons:
	ld [wItemQuantityChange], a
	call TMHMCase_GetCurrentPageSlotCount
	ld [wBuffer1], a
	xor a

.loop
	cp TMHM_CASE_PAGE_LENGTH
	ret nc
	push af
	ld d, a
	ld a, [wBuffer1]
	cp d
	jr z, .clear
	jr c, .clear
	ld a, [wMenuScrollPosition + 3]
	cp d
	jr z, .draw
	jr c, .draw
	ld a, [wItemQuantityChange]
	cp d
	jr z, .draw
	ld a, d
	call TMHMCase_DrawTMHMSlotAttrs
	jr .next

.draw
	ld a, d
	call TMHMCase_DrawTMHMSlot
	jr .next

.clear
	ld a, d
	call TMHMCase_ClearDiscSlotTilesOnly

.next
	pop af
	inc a
	jr .loop

TMHMCase_DrawTMHMSlot:
	push af
	call TMHMCase_GetTMHMSlotPalette
	jr nc, TMHMCase_ClearDiscSlot
	ld d, a
	pop af

TMHMCase_DrawDiscSlot:
	push de
	call TMHMCase_GetIconCoord
	push bc
	call Coord2Tile
	lb bc, 3, 3
	ld a, TMHM_CASE_STATIC_TILE
	call TMHMCase_PlaceTileBlock
	pop bc
	call Coord2Attr
	lb bc, 3, 3
	pop de
	ld a, d
	jp FillBoxWithByte

TMHMCase_DrawTMHMSlotAttrs:
	push af
	call TMHMCase_GetTMHMSlotPalette
	jr nc, .done
	ld d, a
	pop af
	push de
	call TMHMCase_GetIconCoord
	call Coord2Attr
	lb bc, 3, 3
	pop de
	ld a, d
	jp FillBoxWithByte

.done
	pop af
	ret

TMHMCase_GetTMHMSlotPalette:
	ld d, a
	call TMHMCase_GetSlotTMHMNumber
	ret nc
	call TMHMCase_IsCurrentTMHMOwned
	jr c, .owned
	call TMHMCase_GetUnownedDiscPalette
	scf
	ret

.owned
	call TMHMCase_GetSelectedMoveTypeCategory
	jr nc, .default
	ld a, b
	call TMHMCase_GetPageDiscPalette
	scf
	ret

.default
	xor a
	scf
	ret

TMHMCase_ClearSelectedDiscBG:
	ld a, [wMenuCursorPosition]
	call TMHMCase_GetIconCoord
	push bc
	call Coord2Tile
	lb bc, 3, 3
	ld a, ' '
	call ClearBox
	pop bc
	call Coord2Attr
	lb bc, 3, 3
	xor a
	jp FillBoxWithByte

TMHMCase_ClearDiscSlot:
	pop af
	; fallthrough

TMHMCase_ClearDiscSlotTilesOnly:
	call TMHMCase_GetIconCoord
	call Coord2Tile
	lb bc, 3, 3
	ld a, ' '
	jp ClearBox

TMHMCase_BufferDiscBGAtSlot:
	push af
	call TMHMCase_GetSlotTMHMNumber
	jr nc, .done
	call TMHMCase_IsCurrentTMHMOwned
	jr nc, .done
	pop af
	push af
	call TMHMCase_DrawTMHMSlot
	pop af
	call TMHMCase_GetIconCoord
	push bc
	call TMHMCase_BufferDiscBGMapPointers
	pop bc
	call TMHMCase_CopyDiscBGMapBuffers
	ld a, 6
	ldh [hBGMapTileCount], a
	ld a, TRUE
	ldh [hBGMapUpdate], a
	ret

.done
	pop af
	ret

TMHMCase_BufferDiscBGMapPointers:
	call TMHMCase_GetBGMapAddress
	ld de, wBGMapBufferPointers
	ld b, 3

.row
	ld a, l
	ld [de], a
	inc de
	ld a, h
	ld [de], a
	inc de
	ld a, l
	add 2
	ld [de], a
	inc de
	ld a, h
	adc 0
	ld [de], a
	inc de
	ld a, TILEMAP_WIDTH
	add l
	ld l, a
	jr nc, .next
	inc h

.next
	dec b
	jr nz, .row
	ret

TMHMCase_GetBGMapAddress:
	ld hl, vBGMap0
	ld a, b
	and a
	jr z, .got_row
	ld de, TILEMAP_WIDTH

.row
	add hl, de
	dec a
	jr nz, .row

.got_row
	ld e, c
	ld d, 0
	add hl, de
	ret

TMHMCase_CopyDiscBGMapBuffers:
	push bc
	push bc
	call Coord2Tile
	ld de, wBGMapBuffer
	call TMHMCase_CopyDiscBGMapRows
	pop bc
	call Coord2Attr
	ld de, wBGMapPalBuffer
	call TMHMCase_CopyDiscBGMapRows
	pop bc
	ret

TMHMCase_CopyDiscBGMapRows:
	ld b, 3

.row
	ld c, 4

.column
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .column
	push de
	ld de, SCREEN_WIDTH - 4
	add hl, de
	pop de
	dec b
	jr nz, .row
	ret

TMHMCase_GetIconCoord:
	ld hl, TMHMCaseIconCoords
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld c, [hl]
	inc hl
	ld b, [hl]
	ret

TMHMCase_DrawTextboxes:
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

TMHMCase_PlaceTileBlock:
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

TMHMCase_LoadColors:
	ldh a, [hCGB]
	and a
	jr nz, .cgb
	jp SetDefaultBGPAndOBP

.cgb
	ld hl, TMHMCasePalettes
	ld de, wBGPals1
	ld bc, 8 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	ld hl, TMHMCaseCursorPalette
	ld de, wOBPals1 palette 0
	ld bc, 1 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM
	call TMHMCase_LoadNeutralPartyIconPalettes_NoApply
	call TMHMCase_LoadPageDiscPalettes_NoApply
	farcall ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

TMHMCase_LoadPageDiscPalettes_NoApply:
	ldh a, [hCGB]
	and a
	ret z
	call TMHMCase_BuildPageDiscPaletteMap
	ldh a, [rWBK]
	push af
	ld a, BANK(wStringBuffer4)
	ldh [rWBK], a
	ld hl, wStringBuffer4
	ld de, wBGPals1 palette 1
	ld c, TMHM_CASE_PAGE_DISC_PALETTE_COUNT

.loop
	push bc
	push de
	push hl
	ld a, [hl]
	cp $ff
	jr z, .default
	call TMHMCase_GetTypeIconPalette
	jr c, .copy

.default
	ld hl, TMHMCaseCursorPalette

.copy
	pop bc
	pop de
	push bc
	push de
	call TMHMCase_CopyBGPalette
	pop de
	ld hl, 1 palettes
	add hl, de
	ld d, h
	ld e, l
	pop hl
	inc hl
	pop bc
	dec c
	jr nz, .loop
	pop af
	ldh [rWBK], a
	ret

TMHMCase_LoadDefaultMoveInfoIconPalettes:
	ldh a, [hCGB]
	and a
	ret z
	call TMHMCase_LoadDefaultMoveInfoIconPalettes_NoApply
	call TMHMCase_LoadNeutralPartyIconPalettes_NoApply
	jp TMHMCase_ApplyMoveInfoIconPalettes

TMHMCase_LoadSelectedMoveInfoIconPalettes:
	ldh a, [hCGB]
	and a
	ret z
	call TMHMCase_LoadSelectedMoveInfoIconPalettes_NoApply
	call TMHMCase_LoadPartyIconPalettes_NoApply
	jp TMHMCase_ApplyMoveInfoIconPalettes

TMHMCase_LoadCurrentMoveInfoIconPalettes:
	call TMHMCase_GetSelectedTMHMNumber
	ret nc
	call TMHMCase_IsCurrentTMHMOwned
	jp c, TMHMCase_LoadSelectedMoveInfoIconPalettes
	jp TMHMCase_LoadDefaultMoveInfoIconPalettes

TMHMCase_LoadCurrentTypeIconGFX:
	call TMHMCase_GetSelectedMoveTypeCategory
	ret nc
	ld a, b
	call TMHMCase_GetTypeIconGFX
	ret nc
	ld d, h
	ld e, l
	ld hl, vTiles0 tile TMHM_CASE_TYPE_ICON_TILE
	lb bc, BANK(TMHMCaseNormalTypeIconGFX), TMHM_CASE_TYPE_ICON_TILES
	jp Get2bpp

TMHMCase_LoadSelectedMoveInfoIconPalettes_NoApply:
	ldh a, [hCGB]
	and a
	ret z
	call TMHMCase_LoadDefaultMoveInfoIconPalettes_NoApply
	call TMHMCase_GetSelectedMoveTypeCategory
	ret nc
	push bc
	ld a, b
	call TMHMCase_GetTypeIconPalette
	jr nc, .category
	ld de, wOBPals1 palette 0
	call TMHMCase_CopyOAMPalette

	.category
	pop bc
	ld a, c
	call TMHMCase_GetCategoryIconPalette
	ret nc
	ld de, wOBPals1 palette 1
	jp TMHMCase_CopyOAMPalette

TMHMCase_LoadDefaultMoveInfoIconPalettes_NoApply:
	ldh a, [hCGB]
	and a
	ret z
	ld hl, TMHMCaseCursorPalette
	ld de, wOBPals1 palette 0
	call TMHMCase_CopyOAMPalette
	ld hl, TMHMCasePhysicalCategoryIconPalette
	ld de, wOBPals1 palette 1
	jp TMHMCase_CopyOAMPalette

TMHMCase_LoadNeutralPartyIconPalettes_NoApply:
	ld a, [wCurPartyMon]
	push af
	; After page-transition drawing, this byte caches party learnability flags.
	xor a
	ld [wMenuScrollPosition + 3], a
	call TMHMCase_GetPartyCount
	and a
	jr z, .done
	ld b, a
	xor a

.loop
	push af
	push bc
	ld [wCurPartyMon], a
	call TMHMCase_LoadCurrentPartyIconNeutralPalette
	pop bc
	pop af
	inc a
	dec b
	jr nz, .loop

.done
	pop af
	ld [wCurPartyMon], a
	ret

TMHMCase_LoadPartyIconPalettes_NoApply:
	ld a, [wCurPartyMon]
	push af
	ld a, [wCurPartySpecies]
	push af
	xor a
	ld [wMenuScrollPosition + 3], a
	call TMHMCase_SetPutativeTMHMMove
	call TMHMCase_GetPartyCount
	and a
	jr z, .done
	ld b, a
	xor a

.loop
	push af
	push bc
	ld [wCurPartyMon], a
	call TMHMCase_GetPartySpecies
	cp EGG
	jr z, .neutral
	ld [wCurPartySpecies], a
	predef CanLearnTMHMMove
	ld a, c
	and a
	jr z, .neutral
	call TMHMCase_SetCurrentPartyIconLearnFlag
	call TMHMCase_LoadCurrentPartyIconColorPalette
	jr .next

.neutral
	call TMHMCase_LoadCurrentPartyIconNeutralPalette

.next
	pop bc
	pop af
	inc a
	dec b
	jr nz, .loop

.done
	pop af
	ld [wCurPartySpecies], a
	pop af
	ld [wCurPartyMon], a
	ret

TMHMCase_SetCurrentPartyIconLearnFlag:
	ld hl, TMHMCasePartyIconLearnFlags
	ld a, [wCurPartyMon]
	ld e, a
	ld d, 0
	add hl, de
	ld a, [wMenuScrollPosition + 3]
	or [hl]
	ld [wMenuScrollPosition + 3], a
	ret

TMHMCase_SetPutativeTMHMMove:
	ld a, [wTempTMHM]
	push af
	predef GetTMHMMove
	ld a, [wTempTMHM]
	ld [wPutativeTMHMMove], a
	pop af
	ld [wTempTMHM], a
	ret

TMHMCase_LoadCurrentPartyIconNeutralPalette:
	call TMHMCase_GetCurrentPartyIconPaletteSlot
	call TMHMCase_SetCurrentPartyIconOAMAttributes
	ldh a, [hCGB]
	and a
	ret z
	ld a, c
	call TMHMCase_GetOAMPalettePointer
	ld hl, TMHMCaseCursorPalette
	jp TMHMCase_CopyOAMPalette

TMHMCase_LoadCurrentPartyIconColorPalette:
	call TMHMCase_GetCurrentPartyIconPaletteSlot
	call TMHMCase_SetCurrentPartyIconOAMAttributes
	ldh a, [hCGB]
	and a
	ret z
	ld a, c
	push af
	ld a, MON_DVS
	call GetPartyParamLocation
	farcall GetMenuMonIconPalette
	ld d, e
	pop af
	ld c, a
	ld a, d
	jp TMHMCase_CopyPartyMenuOBPalette

TMHMCase_GetCurrentPartyIconPaletteSlot:
	ld a, [wCurPartyMon]
	add TMHM_CASE_PARTY_ICON_PALETTE
	ld c, a
	ret

TMHMCase_SetCurrentPartyIconOAMAttributes:
	ld hl, wShadowOAMSprite16Attributes
	ld a, [wCurPartyMon]
	swap a
	ld e, a
	ld d, 0
	add hl, de
	ld de, OBJ_SIZE
	ld b, 4
	ld a, c

.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	ret

TMHMCase_CopyPartyMenuOBPalette:
; a = PartyMenuOBPals palette, c = destination OBJ palette
	push bc
	call TMHMCase_GetPartyMenuOBPalettePointer
	pop bc
	push hl
	ld a, c
	call TMHMCase_GetOAMPalettePointer
	pop hl
	ld bc, 1 palettes
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld a, BANK(PartyMenuOBPals)
	call FarCopyBytes
	pop af
	ldh [rWBK], a
	ret

TMHMCase_GetPartyMenuOBPalettePointer:
	ld l, a
	ld h, 0
rept 3
	add hl, hl
endr
	ld de, PartyMenuOBPals
	add hl, de
	ret

TMHMCase_GetOAMPalettePointer:
	ld l, a
	ld h, 0
rept 3
	add hl, hl
endr
	ld de, wOBPals1
	add hl, de
	ld d, h
	ld e, l
	ret

TMHMCase_CopyBGPalette:
	ld bc, 1 palettes
	ld a, BANK(wBGPals1)
	jp FarCopyWRAM

TMHMCase_CopyOAMPalette:
	ld bc, 1 palettes
	ld a, BANK(wOBPals1)
	jp FarCopyWRAM

TMHMCase_ApplyMoveInfoIconPalettes:
	farcall ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

TMHMCase_UpdateSelection:
	call TMHMCase_DrawTextboxes
	call TMHMCase_ClearMoveInfoIconOAM
	call TMHMCase_GetSelectedTMHMNumber
	jr c, .got_tmhm
	call ClearSprites
	ret

.got_tmhm
	call TMHMCase_PlaceCursor
	call TMHMCase_PrintSelectedTMHMNumber
	call TMHMCase_IsCurrentTMHMOwned
	jr nc, TMHMCase_PrintUnknownMove
	call TMHMCase_LoadCurrentTypeIconGFX
	call TMHMCase_LoadSelectedMoveInfoIconPalettes
	call TMHMCase_PlacePartyIconOAM
	call TMHMCase_PlaceMoveInfoIcons
	call TMHMCase_ClearSelectedDiscBG
	call TMHMCase_UpdateAnimatedDiscOAM
	jp TMHMCase_PrintSelectedMoveInfo

TMHMCase_UpdateSelection_NoApply:
	call TMHMCase_DrawTextboxes
	call TMHMCase_ClearMoveInfoIconOAM
	call TMHMCase_GetSelectedTMHMNumber
	jr c, .got_tmhm
	call ClearSprites
	ret

.got_tmhm
	call TMHMCase_PlaceCursor
	call TMHMCase_PrintSelectedTMHMNumber
	call TMHMCase_IsCurrentTMHMOwned
	jr nc, TMHMCase_PrintUnknownMove_NoApply
	call TMHMCase_LoadCurrentTypeIconGFX
	call TMHMCase_LoadSelectedMoveInfoIconPalettes_NoApply
	call TMHMCase_LoadPartyIconPalettes_NoApply
	call TMHMCase_PlacePartyIconOAM
	call TMHMCase_PlaceMoveInfoIcons
	call TMHMCase_ClearSelectedDiscBG
	call TMHMCase_UpdateAnimatedDiscOAM
	jp TMHMCase_PrintSelectedMoveInfo

TMHMCase_PrintUnknownMove:
	call TMHMCase_ClearAnimatedDiscOAM
	call TMHMCase_LoadDefaultMoveInfoIconPalettes
	call TMHMCase_PlacePartyIconOAM
	jr TMHMCase_PrintUnknownMoveText

TMHMCase_PrintUnknownMove_NoApply:
	call TMHMCase_ClearAnimatedDiscOAM
	call TMHMCase_LoadDefaultMoveInfoIconPalettes_NoApply
	call TMHMCase_LoadNeutralPartyIconPalettes_NoApply
	call TMHMCase_PlacePartyIconOAM

TMHMCase_PrintUnknownMoveText:
	hlcoord 3, 10
	ld de, TMHMCaseUnknownString
	call PlaceString
	hlcoord 1, 14
	ld de, TMHMCaseUnknownString
	jp PlaceString

TMHMCase_IsCurrentTMHMOwned:
	ld a, [wTempTMHM]
	dec a
	ld c, a
	ld b, 0
	ld hl, wTMsHMs
	add hl, bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wTMsHMs)
	ldh [rWBK], a
	ld a, [hl]
	ld b, a
	pop af
	ldh [rWBK], a
	ld a, b
	and a
	ret z
	scf
	ret

TMHMCase_PrintSelectedTMHMNumber:
	ld a, [wTempTMHM]
	cp NUM_TMS + 1
	jr nc, .hm
	hlcoord 3, 9
	ld de, .TMString
	call PlaceString
	hlcoord 5, 9
	ld de, wTempTMHM
	lb bc, PRINTNUM_LEADINGZEROS | 1, 2
	jp PrintNum

.hm
	hlcoord 3, 9
	ld de, .HMString
	call PlaceString
	ld a, [wTempTMHM]
	sub NUM_TMS
	ld [wItemQuantityChange], a
	hlcoord 5, 9
	ld de, wItemQuantityChange
	lb bc, PRINTNUM_LEADINGZEROS | 1, 2
	jp PrintNum

.TMString:
	db "TM@"
.HMString:
	db "HM@"

TMHMCase_PrintSelectedMove:
	ld a, [wTempTMHM]
	push af
	predef GetTMHMMove
	ld a, [wTempTMHM]
	ld [wNamedObjectIndex], a
	ld [wCurSpecies], a
	call GetMoveName
	hlcoord 3, 10
	ld de, wStringBuffer1
	call PlaceString
	hlcoord 1, 14
	predef PrintMoveDescription
	pop af
	ld [wTempTMHM], a
	ret

TMHMCase_PrintSelectedMoveInfo:
	ld a, [wMenuScrollPosition + 2]
	and a
	jp z, TMHMCase_PrintSelectedMove
	call TMHMCase_PrintSelectedMoveName
	jp TMHMCase_PrintSelectedMoveStats

TMHMCase_PrintSelectedMoveName:
	ld a, [wTempTMHM]
	push af
	predef GetTMHMMove
	ld a, [wTempTMHM]
	ld [wNamedObjectIndex], a
	ld [wCurSpecies], a
	call GetMoveName
	hlcoord 3, 10
	ld de, wStringBuffer1
	call PlaceString
	pop af
	ld [wTempTMHM], a
	ret

TMHMCase_PrintSelectedMoveStats:
	call TMHMCase_PlaceMoveStatIcons
	ld a, [wTempTMHM]
	push af
	predef GetTMHMMove
	call TMHMCase_PrintMovePower
	call TMHMCase_PrintMoveAccuracy
	call TMHMCase_PrintMoveEffectChance
	pop af
	ld [wTempTMHM], a
	ret

TMHMCase_PlaceMoveStatIcons:
	hlcoord 1, 14
	ld a, TMHM_CASE_POWER_TILE
	call TMHMCase_PlaceTwoTileIcon
	hlcoord 7, 14
	ld a, TMHM_CASE_ACCURACY_TILE
	call TMHMCase_PlaceTwoTileIcon
	hlcoord 13, 14
	ld a, TMHM_CASE_EFFECT_CHANCE_TILE

TMHMCase_PlaceTwoTileIcon:
	ld [hli], a
	inc a
	ld [hl], a
	ret

TMHMCase_PrintMovePower:
	ld a, [wTempTMHM]
	ld l, a
	ld a, MOVE_POWER
	call GetMoveAttribute
	hlcoord 3, 14
	cp 2
	jr c, TMHMCase_PrintNoMoveStat
	ld [wBuffer1], a
	ld de, wBuffer1
	lb bc, PRINTNUM_LEFTALIGN | 1, 3
	jp PrintNum

TMHMCase_PrintMoveAccuracy:
	ld a, [wTempTMHM]
	ld l, a
	ld a, MOVE_ACC
	call GetMoveAttribute
	call TMHMCase_ConvertPercentages
	ld [wBuffer1], a
	ld de, wBuffer1
	lb bc, PRINTNUM_LEFTALIGN | 1, 3
	hlcoord 9, 14
	jp PrintNum

TMHMCase_PrintMoveEffectChance:
	ld a, [wTempTMHM]
	ld l, a
	ld a, MOVE_CHANCE
	call GetMoveAttribute
	hlcoord 15, 14
	cp 1
	jr c, TMHMCase_PrintNoMoveStat
	call TMHMCase_ConvertPercentages
	ld [wBuffer1], a
	ld de, wBuffer1
	lb bc, PRINTNUM_LEFTALIGN | 1, 3
	jp PrintNum

TMHMCase_PrintNoMoveStat:
	ld de, TMHMCaseNoMoveStatString
	jp PlaceString

TMHMCase_ConvertPercentages:
	ldh [hMultiplicand + 2], a
	xor a
	ldh [hMultiplicand + 1], a
	ldh [hMultiplicand], a
	ld a, 100
	ldh [hMultiplier], a
	call Multiply
	ldh a, [hProduct + 2]
	and a
	ret z
	inc a
	ret

TMHMCase_GetSelectedMoveTypeCategory:
	ld a, [wTempTMHM]
	push af
	predef GetTMHMMove
	ld a, [wTempTMHM]
	ld l, a
	ld a, MOVE_TYPE
	call GetMoveAttribute
	ld b, a
	ld a, [wTempTMHM]
	ld l, a
	ld a, MOVE_POWER
	call GetMoveAttribute
	cp 2
	jr c, .status
	ld a, b
	cp SPECIAL
	jr nc, .special
	ld c, MOVE_CATEGORY_PHYSICAL
	jr .done

.special
	ld c, MOVE_CATEGORY_SPECIAL
	jr .done

.status
	ld c, MOVE_CATEGORY_STATUS

.done
	pop af
	ld [wTempTMHM], a
	scf
	ret

TMHMCase_GetTypeIconGFX:
	cp TYPES_END
	jr nc, .none
	ld e, a
	ld d, 0
	ld hl, TMHMCaseTypeIconGFXPointers
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, h
	or l
	jr z, .none
	scf
	ret

.none
	and a
	ret

TMHMCase_GetTypeIconPalette:
	cp TYPES_END
	jr nc, .none
	ld e, a
	ld d, 0
	ld hl, TMHMCaseTypeIconPalettePointers
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, h
	or l
	jr z, .none
	scf
	ret

.none
	and a
	ret

TMHMCase_GetCategoryIconTile:
	cp NUM_MOVE_CATEGORIES
	jr nc, .none
	add a
	add TMHM_CASE_CATEGORY_ICON_TILE
	scf
	ret

.none
	and a
	ret

TMHMCase_GetCategoryIconPalette:
	cp NUM_MOVE_CATEGORIES
	jr nc, .none
	ld e, a
	ld d, 0
	ld hl, TMHMCaseCategoryIconPalettePointers
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, h
	or l
	jr z, .none
	scf
	ret

.none
	and a
	ret

TMHMCase_PlaceMoveInfoIcons:
	call TMHMCase_GetSelectedMoveTypeCategory
	ret nc
	push bc
	ld a, b
	call TMHMCase_GetTypeIconGFX
	jr nc, .category
	ld hl, wShadowOAMSprite10
	ld b, TMHM_CASE_TYPE_ICON_Y
	ld c, TMHM_CASE_TYPE_ICON_X
	ld d, TMHM_CASE_TYPE_ICON_TILE
	ld e, 0
	ld a, TMHM_CASE_TYPE_ICON_TILES
	call TMHMCase_PlaceOAMRow

	.category
	pop bc
	ld a, c
	call TMHMCase_GetCategoryIconTile
	ret nc
	ld d, a
	ld hl, wShadowOAMSprite14
	ld b, TMHM_CASE_CATEGORY_ICON_Y
	ld c, TMHM_CASE_CATEGORY_ICON_X
	ld e, 1
	ld a, 2
	jp TMHMCase_PlaceOAMRow

TMHMCase_PlaceOAMRow:
	push af
	ld a, b
	ld [hli], a
	ld a, c
	ld [hli], a
	ld a, d
	ld [hli], a
	inc d
	ld a, e
	ld [hli], a
	ld a, c
	add 8
	ld c, a
	pop af
	dec a
	jr nz, TMHMCase_PlaceOAMRow
	ret

TMHMCase_UpdateAnimatedDiscOAM:
	call TMHMCase_ClearAnimatedDiscOAM
	call TMHMCase_GetSelectedTMHMNumber
	ret nc
	call TMHMCase_IsCurrentTMHMOwned
	ret nc
	ld a, [wMenuScrollPosition + 1]
	srl a
	srl a
	and TMHM_CASE_ANIM_FRAME_COUNT - 1
	ld c, a
	add a
	add a
	add a
	add c
	add TMHM_CASE_ANIM_TILE
	ld d, a
	ld a, [wMenuCursorPosition]
	call TMHMCase_GetDiscOAMCoords
	ld hl, wShadowOAMSprite01
	jp TMHMCase_PlaceDiscOAM

TMHMCase_GetDiscOAMCoords:
	call TMHMCase_GetIconCoord
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
	ret

TMHMCase_PlaceDiscOAM:
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
	xor a
	ld [hli], a
	ld a, b
	ld [hli], a
	ld a, c
	add 8
	ld [hli], a
	ld a, d
	ld [hli], a
	inc d
	xor a
	ld [hli], a
	ld a, b
	ld [hli], a
	ld a, c
	add 16
	ld [hli], a
	ld a, d
	ld [hli], a
	inc d
	xor a
	ld [hli], a
	ret

TMHMCase_ClearAnimatedDiscOAM:
	ld hl, wShadowOAMSprite01YCoord
	ld de, OBJ_SIZE
	ld b, TMHM_CASE_ANIM_OAM_COUNT
	xor a

.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	ret

TMHMCase_ClearMoveInfoIconOAM:
	ld hl, wShadowOAMSprite10YCoord
	ld de, OBJ_SIZE
	ld b, TMHM_CASE_MOVE_INFO_ICON_OAM_COUNT
	xor a

.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	ret

TMHMCase_LoadPartyIconGFX:
	call TMHMCase_GetPartyCount
	and a
	ret z
	ld b, a
	xor a

.loop
	push af
	push bc
	push af
	add a
	add a
	add a
	add TMHM_CASE_PARTY_ICON_TILE
	ld [wCurIconTile], a
	pop af
	call TMHMCase_GetPartySpecies
	ld e, a
	farcall LoadOverworldMonIcon
	ld a, [wCurIconTile]
	call TMHMCase_GetVRAMTileAddress
	ld c, TMHM_CASE_PARTY_ICON_TILES
	call Get2bpp
	pop bc
	pop af
	inc a
	dec b
	jr nz, .loop
	xor a
	ldh [hObjectStructIndex], a
	ret

TMHMCase_GetVRAMTileAddress:
	ld l, a
	ld h, 0
rept 4
	add hl, hl
endr
	push de
	ld de, vTiles0
	add hl, de
	pop de
	ret

TMHMCase_PlacePartyIconOAM:
	call TMHMCase_ClearPartyIconOAM
	call TMHMCase_GetPartyCount
	and a
	ret z
	ld b, a
	xor a

.loop
	push af
	push bc
	ldh [hObjectStructIndex], a
	call TMHMCase_GetCurrentPartyIconTile
	ld [wCurIconTile], a
	ldh a, [hObjectStructIndex]
	call TMHMCase_GetPartyIconOAMCoords
	ld hl, wShadowOAMSprite16
	ldh a, [hObjectStructIndex]
	swap a
	ld e, a
	ld d, 0
	add hl, de
	ld a, [wCurIconTile]
	ld d, a
	ldh a, [hObjectStructIndex]
	add TMHM_CASE_PARTY_ICON_PALETTE
	ld e, a
	call TMHMCase_PlacePartyIconOAMBlock
	pop bc
	pop af
	inc a
	dec b
	jr nz, .loop
	ret

TMHMCase_GetCurrentPartyIconTile:
	ld b, a
	add a
	add a
	add a
	add TMHM_CASE_PARTY_ICON_TILE
	ld c, a
	push bc
	ld a, b
	call TMHMCase_CanCurrentPartyIconAnimate
	pop bc
	ld a, c
	ret nc
	ld hl, wMenuScrollPosition + 1
	bit 3, [hl]
	ret z
	add 4
	ret

TMHMCase_CanCurrentPartyIconAnimate:
	ld hl, TMHMCasePartyIconLearnFlags
	ld e, a
	ld d, 0
	add hl, de
	ld a, [wMenuScrollPosition + 3]
	and [hl]
	ret z
	scf
	ret

TMHMCase_PlacePartyIconOAMBlock:
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
	ret

TMHMCase_ClearPartyIconOAM:
	ld hl, wShadowOAMSprite16YCoord
	ld de, OBJ_SIZE
	ld b, TMHM_CASE_PARTY_ICON_OAM_COUNT
	xor a

.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	ret

TMHMCase_HideUseMenuPartyIconOAM:
; The Use/Quit menu only overlaps the lower half of party slot 5 and all of slot 6.
	xor a
	ld [wShadowOAMSprite15YCoord], a
	ld hl, wShadowOAMSprite34YCoord
	ld de, OBJ_SIZE
	ld b, 6

.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	ret

TMHMCase_RestoreUseMenuCategoryOAM:
	call TMHMCase_GetSelectedMoveTypeCategory
	ret nc
	ld a, c
	call TMHMCase_GetCategoryIconTile
	ret nc
	inc a
	ld d, a
	ld hl, wShadowOAMSprite15
	ld a, TMHM_CASE_CATEGORY_ICON_Y
	ld [hli], a
	ld a, TMHM_CASE_CATEGORY_ICON_X + 8
	ld [hli], a
	ld a, d
	ld [hli], a
	ld a, 1
	ld [hli], a
	ret

TMHMCase_GetPartyCount:
	ldh a, [rWBK]
	push af
	ld a, BANK(wPartyCount)
	ldh [rWBK], a
	ld a, [wPartyCount]
	ld b, a
	pop af
	ldh [rWBK], a
	ld a, b
	ret

TMHMCase_GetPartySpecies:
	push bc
	ld c, a
	ld b, 0
	ldh a, [rWBK]
	push af
	ld a, BANK(wPartySpecies)
	ldh [rWBK], a
	ld hl, wPartySpecies
	add hl, bc
	ld b, [hl]
	pop af
	ldh [rWBK], a
	ld a, b
	pop bc
	ret

TMHMCase_GetPartyIconOAMCoords:
	ld hl, TMHMCasePartyIconCoords
	ld c, a
	ld b, 0
	add hl, bc
	add hl, bc
	ld a, [hli]
	add a
	add a
	add a
	add 8
	ld c, a
	ld a, [hl]
	add a
	add a
	add a
	add 16
	ld b, a
	ret

TMHMCase_AdvanceAnimTimer:
	ld hl, wMenuScrollPosition + 1
	inc [hl]
	ret

TMHMCase_PlaceCursor:
	ld hl, TMHMCaseCursorPositions
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

TMHMCaseIconCoords:
	db 3, 2
	db 7, 2
	db 11, 2
	db 15, 2
	db 3, 5
	db 7, 5
	db 11, 5
	db 15, 5

TMHMCaseCursorPositions:
	db 17, 24
	db 49, 24
	db 81, 24
	db 113, 24
	db 17, 48
	db 49, 48
	db 81, 48
	db 113, 48

TMHMCasePartyIconCoords:
	db 0, 3
	db 0, 6
	db 0, 9
	db 18, 3
	db 18, 6
	db 18, 9

TMHMCasePartyIconLearnFlags:
	db %000001
	db %000010
	db %000100
	db %001000
	db %010000
	db %100000

TMHMCasePalettes:
; Palette 0: text, black/white title tiles, header, and green side borders
	RGB 31, 31, 31
	RGB TMHM_CASE_GREEN_LIGHT_R, TMHM_CASE_GREEN_LIGHT_G, TMHM_CASE_GREEN_LIGHT_B
	RGB TMHM_CASE_GREEN_DARK_R, TMHM_CASE_GREEN_DARK_G, TMHM_CASE_GREEN_DARK_B
	RGB 00, 00, 00

; Palettes 1-7: TM/HM discs, loaded dynamically per page
	rept TMHM_CASE_PAGE_DISC_PALETTE_COUNT
	RGB 31, 31, 31
	RGB 21, 21, 21
	RGB 10, 10, 10
	RGB 00, 00, 00
	endr

TMHMCaseCursorPalette:
INCLUDE "gfx/items/tmhm/tmhm_static.pal"

TMHMCaseUnknownString:
	db "???@"

TMHMCaseNoMoveStatString:
	db "---@"

TMHMCaseUseMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 13, 7, SCREEN_WIDTH - 1, TEXTBOX_Y - 1
	dw .MenuData
	db 1 ; default option

.MenuData:
	db STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING ; flags
	db 2 ; items
	db "USE@"
	db "QUIT@"

TMHMCaseYouDontHaveAMonText:
	text_far _YouDontHaveAMonText
	text_end

TMHMCaseBootedTMText:
	text_far _BootedTMText
	text_end

TMHMCaseBootedHMText:
	text_far _BootedHMText
	text_end

TMHMCaseContainedMoveText:
	text_far _ContainedMoveText
	text_end

TMHMCaseTypeIconGFXPointers:
	table_width 2
	dw TMHMCaseNormalTypeIconGFX
	dw TMHMCaseFightingTypeIconGFX
	dw TMHMCaseFlyingTypeIconGFX
	dw TMHMCasePoisonTypeIconGFX
	dw TMHMCaseGroundTypeIconGFX
	dw TMHMCaseRockTypeIconGFX
	dw 0 ; BIRD
	dw TMHMCaseBugTypeIconGFX
	dw TMHMCaseDarkTypeIconGFX
	dw TMHMCaseSteelTypeIconGFX
	rept CURSE_TYPE - UNUSED_TYPES
	dw 0
	endr
	dw 0 ; CURSE_TYPE
	dw TMHMCaseFireTypeIconGFX
	dw TMHMCaseWaterTypeIconGFX
	dw TMHMCaseGrassTypeIconGFX
	dw TMHMCaseElectricTypeIconGFX
	dw TMHMCasePsychicTypeIconGFX
	dw TMHMCaseIceTypeIconGFX
	dw TMHMCaseDragonTypeIconGFX
	dw TMHMCaseGhostTypeIconGFX
	dw TMHMCaseFairyTypeIconGFX
	assert_table_length TYPES_END

TMHMCaseTypeIconPalettePointers:
	table_width 2
	dw TMHMCaseNormalTypeIconPalette
	dw TMHMCaseFightingTypeIconPalette
	dw TMHMCaseFlyingTypeIconPalette
	dw TMHMCasePoisonTypeIconPalette
	dw TMHMCaseGroundTypeIconPalette
	dw TMHMCaseRockTypeIconPalette
	dw 0 ; BIRD
	dw TMHMCaseBugTypeIconPalette
	dw TMHMCaseDarkTypeIconPalette
	dw TMHMCaseSteelTypeIconPalette
	rept CURSE_TYPE - UNUSED_TYPES
	dw 0
	endr
	dw 0 ; CURSE_TYPE
	dw TMHMCaseFireTypeIconPalette
	dw TMHMCaseWaterTypeIconPalette
	dw TMHMCaseGrassTypeIconPalette
	dw TMHMCaseElectricTypeIconPalette
	dw TMHMCasePsychicTypeIconPalette
	dw TMHMCaseIceTypeIconPalette
	dw TMHMCaseDragonTypeIconPalette
	dw TMHMCaseGhostTypeIconPalette
	dw TMHMCaseFairyTypeIconPalette
	assert_table_length TYPES_END

TMHMCaseCategoryIconPalettePointers:
	table_width 2
	dw TMHMCasePhysicalCategoryIconPalette
	dw TMHMCaseSpecialCategoryIconPalette
	dw TMHMCaseStatusCategoryIconPalette
	assert_table_length NUM_MOVE_CATEGORIES

TMHMCaseAnimGFX:
INCBIN "gfx/items/tmhm/tmhm_frame_1.2bpp"
INCBIN "gfx/items/tmhm/tmhm_frame_2.2bpp"
INCBIN "gfx/items/tmhm/tmhm_frame_3.2bpp"
INCBIN "gfx/items/tmhm/tmhm_frame_4.2bpp"

TMHMCaseNormalTypeIconGFX:
INCBIN "gfx/types/compact/normal_compact.2bpp"
TMHMCaseFightingTypeIconGFX:
INCBIN "gfx/types/compact/fighting_compact.2bpp"
TMHMCaseFlyingTypeIconGFX:
INCBIN "gfx/types/compact/flying_compact.2bpp"
TMHMCasePoisonTypeIconGFX:
INCBIN "gfx/types/compact/poison_compact.2bpp"
TMHMCaseGroundTypeIconGFX:
INCBIN "gfx/types/compact/ground_compact.2bpp"
TMHMCaseRockTypeIconGFX:
INCBIN "gfx/types/compact/rock_compact.2bpp"
TMHMCaseBugTypeIconGFX:
INCBIN "gfx/types/compact/bug_compact.2bpp"
TMHMCaseDarkTypeIconGFX:
INCBIN "gfx/types/compact/dark_compact.2bpp"
TMHMCaseSteelTypeIconGFX:
INCBIN "gfx/types/compact/steel_compact.2bpp"
TMHMCaseFireTypeIconGFX:
INCBIN "gfx/types/compact/fire_compact.2bpp"
TMHMCaseWaterTypeIconGFX:
INCBIN "gfx/types/compact/water_compact.2bpp"
TMHMCaseGrassTypeIconGFX:
INCBIN "gfx/types/compact/grass_compact.2bpp"
TMHMCaseElectricTypeIconGFX:
INCBIN "gfx/types/compact/electric_compact.2bpp"
TMHMCasePsychicTypeIconGFX:
INCBIN "gfx/types/compact/psychic_compact.2bpp"
TMHMCaseIceTypeIconGFX:
INCBIN "gfx/types/compact/ice_compact.2bpp"
TMHMCaseDragonTypeIconGFX:
INCBIN "gfx/types/compact/dragon_compact.2bpp"
TMHMCaseGhostTypeIconGFX:
INCBIN "gfx/types/compact/ghost_compact.2bpp"
TMHMCaseFairyTypeIconGFX:
INCBIN "gfx/types/compact/fairy_compact.2bpp"

TMHMCaseCategoryIconGFX:
TMHMCasePhysicalCategoryIconGFX:
INCBIN "gfx/move_categories/compact/physical_compact.2bpp"
TMHMCaseSpecialCategoryIconGFX:
INCBIN "gfx/move_categories/compact/special_compact.2bpp"
TMHMCaseStatusCategoryIconGFX:
INCBIN "gfx/move_categories/compact/status_compact.2bpp"

TMHMCasePowerIconGFX:
INCBIN "gfx/font/power.2bpp"

TMHMCaseAccuracyIconGFX:
INCBIN "gfx/font/accuracy.2bpp"

TMHMCaseEffectChanceIconGFX:
INCBIN "gfx/font/effect_chance.2bpp"

TMHMCaseStaticGFX:
INCBIN "gfx/items/tmhm/tmhm_static.2bpp"
TMHMCaseTitleGFX:
INCBIN "gfx/items/tmhm/tmhm_case_title.2bpp"

TMHMCaseHeaderGFX:
	rept 16
	db %11111111
	endr

TMHMCaseNormalTypeIconPalette:
	RGB 31, 31, 31
	RGB 15, 15, 11
	RGB 21, 21, 15
	RGB  0,  0,  0

TMHMCaseFightingTypeIconPalette:
	RGB 31, 31, 31
	RGB 21,  4,  0
	RGB 29,  6,  0
	RGB  0,  0,  0

TMHMCaseFlyingTypeIconPalette:
	RGB 31, 31, 31
	RGB 15, 13, 22
	RGB 21, 18, 30
	RGB  0,  0,  0

TMHMCasePoisonTypeIconPalette:
	RGB 31, 31, 31
	RGB 14,  6, 14
	RGB 20,  8, 20
	RGB  0,  0,  0

TMHMCaseGroundTypeIconPalette:
	RGB 31, 31, 31
	RGB 20, 17,  9
	RGB 28, 24, 13
	RGB  0,  0,  0

TMHMCaseRockTypeIconPalette:
	RGB 31, 31, 31
	RGB 17, 14,  5
	RGB 23, 20,  7
	RGB  0,  0,  0

TMHMCaseBugTypeIconPalette:
	RGB 31, 31, 31
	RGB 15, 17,  3
	RGB 21, 23,  4
	RGB  0,  0,  0

TMHMCaseDarkTypeIconPalette:
	RGB 31, 31, 31
	RGB 10,  8,  7
	RGB 14, 11,  9
	RGB  0,  0,  0

TMHMCaseSteelTypeIconPalette:
	RGB 31, 31, 31
	RGB 17, 17, 19
	RGB 23, 23, 26
	RGB  0,  0,  0

TMHMCaseFireTypeIconPalette:
	RGB 31, 31, 31
	RGB 22, 12,  4
	RGB 30, 16,  6
	RGB  0,  0,  0

TMHMCaseWaterTypeIconPalette:
	RGB 31, 31, 31
	RGB  9, 13, 22
	RGB 13, 18, 30
	RGB  0,  0,  0

TMHMCaseGrassTypeIconPalette:
	RGB 31, 31, 31
	RGB 11, 18,  7
	RGB 15, 25, 10
	RGB  0,  0,  0

TMHMCaseElectricTypeIconPalette:
	RGB 31, 31, 31
	RGB 22, 19,  4
	RGB 31, 26,  6
	RGB  0,  0,  0

TMHMCasePsychicTypeIconPalette:
	RGB 31, 31, 31
	RGB 22,  8, 12
	RGB 31, 11, 17
	RGB  0,  0,  0

TMHMCaseIceTypeIconPalette:
	RGB 31, 31, 31
	RGB 14, 20, 20
	RGB 19, 27, 27
	RGB  0,  0,  0

TMHMCaseDragonTypeIconPalette:
	RGB 31, 31, 31
	RGB 10,  5, 22
	RGB 14,  7, 31
	RGB  0,  0,  0

TMHMCaseGhostTypeIconPalette:
	RGB 31, 31, 31
	RGB 10,  8, 14
	RGB 14, 11, 19
	RGB  0,  0,  0

TMHMCaseFairyTypeIconPalette:
	RGB 31, 31, 31
	RGB 17, 12, 17
	RGB 23, 16, 23
	RGB  0,  0,  0

TMHMCasePhysicalCategoryIconPalette:
INCLUDE "gfx/move_categories/physical.pal"
TMHMCaseSpecialCategoryIconPalette:
INCLUDE "gfx/move_categories/special.pal"
TMHMCaseStatusCategoryIconPalette:
INCLUDE "gfx/move_categories/status.pal"
