; Listing presentation is independent of the temporary New/Old/ABC ordering.
; Selected Mon, its timelines, streaming producer, and audio owner are shared.
Pokedex_InitListingPresentation:
	ld a, [wPokedexListingPresentation]
	and a
	jr nz, .legacy
	farcall Pokedex_InitGridCursorPosition
	ret
.legacy
	ld a, POKEDEX_LEGACY_HEIGHT
	ld [wDexListingHeight], a
	farcall Pokedex_InitCursorPosition
	ret

PokedexLegacy_LoadStaticGFX:
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
; The normal CGB Dex footprint is in bank 1; reuse its unused DMG UI cells.
	ld de, PokedexLegacyGFX
	ld hl, vTiles2 tile POKEDEX_LEGACY_JUNCTION_TILE
	lb bc, BANK(PokedexLegacyGFX), 3
	call Get2bpp
	ld de, PokedexLegacyGFX + 3 tiles
	ld hl, vTiles2 tile POKEDEX_LEGACY_ARROW_TILE
	lb bc, BANK(PokedexLegacyGFX), 1
	call Get2bpp
	pop af
	ldh [rVBK], a
	ret

PokedexLegacyGFX:
INCBIN "gfx/pokedex/pokedex.2bpp", 64 tiles, 4 tiles
.end
ASSERT .end - PokedexLegacyGFX == 4 tiles

PokedexLegacy_InitMainScreen:
	ld a, POKEDEX_LEGACY_HEIGHT
	ld [wDexListingHeight], a
	xor a
	ldh [hVBlank], a
	ldh [hBGMapMode], a
	ld a, TRUE
	ldh [hOAMUpdate], a
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_LEAVING
	jr z, .stage
	cp DEXSELECT_STATE_MENU_RETURN
	jr z, .stage
	ld a, $a7
	ldh [hWX], a
	call ClearPalettes
	call DelayFrame
.stage
	call ClearSprites
	call PokedexLegacy_DrawWindow
	farcall Pokedex_CopyBackingToWindow
	call PokedexLegacy_DrawSidebar
	ld a, POKEDEX_SCX
	ldh [hSCX], a
	xor a
	ldh [hWY], a
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_LEAVING
	jr z, .return_layout
	farcall Pokedex_PrepareAndCommitSelectedMonGFX
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_MENU_RETURN
	jr z, .return_layout
	farcall Pokedex_GetDexSGBLayout
	jr .layout_ready
.return_layout
	farcall CGB_PokedexStageListLayout
.layout_ready
	xor a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	farcall Pokedex_PublishOrStageListingBacking
	farcall Pokedex_RecordRenderedSelectionKey
	call PokedexLegacy_UpdateOAM
	call PokedexLegacy_DrawWindow
	farcall Pokedex_StartAnimationPrefetch
	farcall Pokedex_RevealOrCommitListing
.revealed
	ld a, VBLANK_POKEDEX
	ldh [hVBlank], a
	xor a
	ld [wPokedexSelectedState], a
	farcall Pokedex_IncrementDexPointer
	ret

PokedexLegacy_UpdateMainScreen:
	call PokedexLegacy_HandleDPadInput
	jr c, .changed
	farcall Pokedex_ServiceAnimationProducer
	ret
.changed
	farcall Pokedex_CancelAnimationPrefetch
	xor a
	ldh [hBGMapMode], a
	farcall Pokedex_PrepareSelectedMonTiles
	farcall CGB_PokedexPrepareFrontpicPalette
	ld a, TRUE
	ldh [hOAMUpdate], a
	call PokedexLegacy_DrawWindow
	call PokedexLegacy_UpdateOAM
	farcall Pokedex_StageOwnerTransitionMaps
; The portrait has already passed before its upload. Publish names and the
; cursor during the following VBlank, so the next portrait scan is coherent.
.wait_portrait
	ldh a, [rLY]
	cp 64
	jr c, .wait_portrait
	cp 78
	jr nc, .wait_portrait
	call PokedexLegacy_CommitPortrait
	farcall CGB_PokedexCommitFrontpicPalette
	di
.wait_oam
	ldh a, [rLY]
	cp 144
	jr c, .wait_oam
	call PokedexLegacy_CommitWindow
	call hTransferShadowOAM
	ei
	xor a
	ldh [hOAMUpdate], a
	farcall Pokedex_RecordRenderedSelectionKey
	ld a, [wCurPartySpecies]
	cp POKEDEX_RENDER_KEY_UNSEEN
	jr z, .footprint_ready
; Update the hidden footprint only after the visible selection is coherent.
; Its staging aliases warm animation work, so finish before warming restarts.
	farcall Pokedex_TransferPreparedFootprint
	ld a, [wCurPartySpecies]
	ld [wPokedexResidentFootprintSpecies], a
.footprint_ready
	farcall Pokedex_StartAnimationPrefetch
	ret

PokedexLegacy_HandleDPadInput:
	farcall Pokedex_ListingHandleDPadInput
	ret c
; Only main Legacy Listing wraps; Search keeps the shared bounded controller.
	ld a, [wDexListingEnd]
	ld l, a
	ld a, [wDexListingEnd + 1]
	ld h, a
	or l
	ret z
	dec hl
	ld a, h
	or l
	ret z
	ldh a, [hJoyLast]
	bit B_PAD_UP, a
	jr nz, .bottom
	bit B_PAD_DOWN, a
	jr z, .unchanged
	xor a
	ld [wDexListingCursor], a
	ld [wDexListingScrollOffset], a
	ld [wDexListingScrollOffset + 1], a
	scf
	ret
.bottom
	ld a, h
	and a
	jr nz, .full_page
	ld a, l
	cp POKEDEX_LEGACY_HEIGHT
	jr nc, .full_page
	ld [wDexListingCursor], a
	xor a
	ld [wDexListingScrollOffset], a
	ld [wDexListingScrollOffset + 1], a
	scf
	ret
.full_page
	ld a, POKEDEX_LEGACY_HEIGHT - 1
	ld [wDexListingCursor], a
	ld de, -(POKEDEX_LEGACY_HEIGHT - 1)
	add hl, de
	ld a, l
	ld [wDexListingScrollOffset], a
	ld a, h
	ld [wDexListingScrollOffset + 1], a
	scf
	ret
.unchanged
	and a
	ret

PokedexLegacy_CommitPortrait:
; The footprint is hidden in Listing. Invalidate its temporary species-ID tag:
; the indirection cache can reuse an ID while scrolling to another species.
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles2
	ld c, 7 * 7
	call Pokedex_HDMATransferFrontpic
	pop af
	ldh [rVBK], a
	xor a
	ld [wPokedexResidentFootprintSpecies], a
	ret

PokedexLegacy_CommitWindow:
; Prepared maps use the existing owner overlay. Both maps and shadow OAM
; publish in one protected VBlank; the generic stack copy can span a frame.
	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	ld a, BANK(wPokedexOwnerAttrmapBuffer)
	ldh [rSVBK], a
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexOwnerAttrmapBuffer
	call .TransferMap
	xor a
	ldh [rVBK], a
	ld hl, wPokedexOwnerTilemapBuffer
	call .TransferMap
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ret
.TransferMap:
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	ldh [rVDMA_SRC_LOW], a
	ld a, HIGH(vBGMap1) & $1f
	ldh [rVDMA_DEST_HIGH], a
	xor a
	ldh [rVDMA_DEST_LOW], a
	ld a, 2 * SCREEN_HEIGHT - 1
	ldh [rVDMA_LEN], a
	ret

PokedexLegacy_DrawSidebar:
	farcall Pokedex_DrawMainScreenBG
; These cells contain both the portrait's right edge and Listing's left edge.
	hlcoord 8, 0
	ld [hl], POKEDEX_LEGACY_CAP_TILE
	hlcoord 8, 1
	ld b, 7
	ld a, POKEDEX_LEGACY_DIVIDER_TILE
	call PokedexLegacy_FillColumn
	hlcoord 7, 8
	ld [hl], POKEDEX_RESIDENT_JOINED_MIDDLE_TILE
	inc hl
	ld [hl], POKEDEX_LEGACY_JUNCTION_TILE
	hlcoord 7, 9
	ld b, 7
	ld a, $7f
	call PokedexLegacy_FillColumn
	hlcoord 8, 9
	ld b, 7
	ld a, POKEDEX_LEGACY_DIVIDER_TILE
	call PokedexLegacy_FillColumn
	hlcoord 7, 16
	ld [hl], $39
	inc hl
	ld [hl], POKEDEX_LEGACY_CAP_TILE
	ret

PokedexLegacy_DrawWindow:
	ldh a, [rSVBK]
	push af
	ld a, $32
	hlcoord 0, 0
	ld bc, SCREEN_AREA
	call ByteFill
	xor a
	hlcoord 0, 0, wAttrmap
	ld bc, SCREEN_AREA
	call ByteFill
	hlcoord 0, 1
	lb bc, 15, 11
	call ClearBox
	hlcoord 0, 0
	ld a, $34
	ld bc, 11
	call ByteFill
	hlcoord 0, 16
	ld a, $39
	ld bc, 11
	call ByteFill
	hlcoord 5, 0
	ld [hl], POKEDEX_LEGACY_ARROW_TILE
	hlcoord 5, 16
	ld [hl], POKEDEX_LEGACY_ARROW_TILE
	hlcoord 5, 16, wAttrmap
	ld [hl], BG_YFLIP
	hlcoord 11, 0
	ld [hl], $50
	hlcoord 11, 1
	ld a, $51
	ld b, 15
	call PokedexLegacy_FillColumn
	ld [hl], $52
	hlcoord 0, 17
	push hl
	ld hl, String_START_OPTION
	ld de, wPokedexNameBuffer
	ld bc, MON_NAME_LENGTH
	ld a, BANK(String_START_OPTION)
	call FarCopyBytes
	pop hl
	ld de, wPokedexNameBuffer
	call PokedexLegacy_PlaceTiles
	xor a
	hlcoord 1, 2
.row
	push af
	push hl
	call PokedexLegacy_GetRowSpecies
	ld a, d
	or e
	jr z, .next
	push de
	ld a, BANK(wPokedexSeen)
	ldh [rSVBK], a
	call CheckSeenMonIndex
	pop de
	pop hl
	push hl
	jr z, .unseen
	push hl
	ld h, d
	ld l, e
	add hl, hl
	add hl, hl
	add hl, de
	add hl, hl
	ld de, PokemonNames - (MON_NAME_LENGTH - 1)
	add hl, de
	ld a, BANK(PokemonNames)
	ld bc, MON_NAME_LENGTH - 1
	ld de, wPokedexNameBuffer
	call FarCopyBytes
	ld a, '@'
	ld [wPokedexNameBuffer + MON_NAME_LENGTH - 1], a
	pop hl
	ld de, wPokedexNameBuffer
	jr .print
.unseen
	ld de, .Unseen
.print
	call PlaceString
.next
	pop hl
	ld bc, 2 * SCREEN_WIDTH
	add hl, bc
	pop af
	inc a
	cp POKEDEX_LEGACY_HEIGHT
	jr c, .row
	pop af
	ldh [rSVBK], a
	ret
.Unseen:
	db "-----@"

PokedexLegacy_GetRowSpecies:
; a = visible row; de = permanent species index, or zero beyond the list.
	ld c, a
	ld b, 0
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a
	add hl, bc
	ld a, [wDexListingEnd + 1]
	cp h
	jr c, .absent
	jr nz, .present
	ld a, [wDexListingEnd]
	cp l
	jr c, .absent
	jr z, .absent
.present
	add hl, hl
	ld bc, wPokedexOrder
	add hl, bc
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	ld a, [hli]
	ld e, a
	ld d, [hl]
	pop af
	ldh [rSVBK], a
	ret
.absent
	ld de, 0
	ret

PokedexLegacy_UpdateOAM:
	ldh a, [rSVBK]
	push af
	call ClearSprites
	ld de, wShadowOAM
	ld a, [wDexListingCursor]
	swap a
	add 24
	ld b, a
	ld c, 72
	ld a, 0
	call .Corner
	ld c, 151
	ld a, OAM_XFLIP
	call .Corner
	ld a, b
	add 15
	ld b, a
	ld c, 72
	ld a, OAM_YFLIP
	call .Corner
	ld c, 151
	ld a, OAM_XFLIP | OAM_YFLIP
	call .Corner
	xor a
.ball
	push af
	push de
	call PokedexLegacy_GetRowSpecies
	ld a, d
	or e
	jr z, .no_ball
	ld a, BANK(wPokedexCaught)
	ldh [rSVBK], a
	call CheckCaughtMonIndex
	jr z, .no_ball
	pop de
	pop af
	push af
	swap a
	add 32
	ld [de], a
	inc de
	ld a, 71
	ld [de], a
	inc de
	ld a, POKEDEX_CAUGHT_BALL_TILE
	ld [de], a
	inc de
	ld a, 1
	ld [de], a
	inc de
	jr .next
.no_ball
	pop de
.next
	pop af
	inc a
	cp POKEDEX_LEGACY_HEIGHT
	jr c, .ball
	push de
	farcall Pokedex_PutScrollbarOAM
	pop hl
	ld bc, 3
	add hl, bc
	ld [hl], 5
	pop af
	ldh [rSVBK], a
	ret
.Corner:
	push af
	ld a, b
	ld [de], a
	inc de
	ld a, c
	ld [de], a
	inc de
	ld a, POKEDEX_LIST_CURSOR_TILE
	ld [de], a
	inc de
	pop af
	ld [de], a
	inc de
	ret

DEF DEXMENU_MODERN EQU 0
DEF DEXMENU_LEGACY EQU 1
DEF DEXMENU_UNOWN EQU 2
DEF DEXMENU_MOVES EQU 3
DEF DEXMENU_TYPES EQU 4
ASSERT DEXMENU_MODERN == DEXLIST_MODERN
ASSERT DEXMENU_LEGACY == DEXLIST_LEGACY

PokedexListing_BeginMenuTransition:
; Hide both BG and OBJ before changing scroll, Window, maps or shared tiles.
; Preserve source palettes; only the hardware targets become a black mask.
	xor a
	ldh [hVBlank], a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	ld a, TRUE
	ldh [hOAMUpdate], a
	call ClearSprites
	ldh a, [hCGB]
	and a
	jr z, .dmg
	ldh a, [rSVBK]
	push af
	ld a, BANK(wBGPals2)
	ldh [rSVBK], a
	ld hl, wBGPals2
	ld bc, 16 palettes
	xor a
	call ByteFill
	pop af
	ldh [rSVBK], a
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	jr .hide
.dmg
	ld a, $ff
	ldh [rBGP], a
.hide
	xor a
	ldh [hOAMUpdate], a
	call DelayFrame
	ld a, TRUE
	ldh [hOAMUpdate], a
	xor a
	ldh [hSCX], a
	ldh [hSCY], a
	ldh [hWY], a
	ld a, $a7
	ldh [hWX], a
	ret

PokedexListing_RevealMenu:
; Called only after map/attrmap uploads and the final palette targets exist.
	xor a
	ldh [hOAMUpdate], a
	call DelayFrame
	ret

PokedexListing_InitModeScreen:
	xor a
	ldh [hBGMapMode], a
	call ClearSprites
	hlcoord 0, 0
	ld a, $31
	ld bc, SCREEN_AREA
	call ByteFill
	hlcoord 0, 2
	lb bc, 9, 18
	call PokedexLegacy_PlaceBorder
	hlcoord 0, 13
	lb bc, 3, 18
	call PokedexLegacy_PlaceBorder
	hlcoord 0, 1
	ld de, .Title
	call PokedexLegacy_PlaceTiles
	hlcoord 3, 3
	ld de, .Modern
	call PlaceString
	hlcoord 3, 5
	ld de, .Legacy
	call PlaceString
	hlcoord 3, 7
	ld a, [wUnlockedUnownMode]
	and a
	jr z, .moves
	ld de, .Unown
	call PlaceString
	ld de, 2 * SCREEN_WIDTH
	add hl, de
.moves
	ld de, .Moves
	call PlaceString
	ld de, 2 * SCREEN_WIDTH
	add hl, de
	ld de, .Types
	call PlaceString
	farcall Pokedex_InitArrowCursor
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_UNOWN_RETURN
	ld a, DEXMENU_UNOWN
	jr z, .cursor
	ld a, [wPokedexListingPresentation]
.cursor
	ld [wDexArrowCursorPosIndex], a
	ld b, a
	hlcoord 2, 3
	and a
	jr z, .arrow_ready
	ld de, 2 * SCREEN_WIDTH
.arrow_row
	add hl, de
	dec b
	jr nz, .arrow_row
.arrow_ready
	ld [hl], '▶'
	xor a
	ld [wPokedexSelectedState], a
	call PokedexListing_ModeDescription
	call WaitBGMap
	ld b, SCGB_POKEDEX_SEARCH_OPTION
	call GetSGBLayout
	farcall Pokedex_ApplyUsualPals
	call PokedexListing_RevealMenu
	farcall Pokedex_IncrementDexPointer
	ret
.Title:
	db $3b, " Modes ", $3c, -1
.Modern:
	db "Modern Dex Mode@"
.Legacy:
	db "Legacy Dex Mode@"
.Unown:
	db "Unown Dex Mode@"
.Moves:
	db "Moves Dex Mode@"
.Types:
	db "Type Matchups@"

PokedexListing_UpdateModeScreen:
	ld hl, .Cursor
	ld de, wPokedexWRAM0Scratch
	ld bc, 12
	call CopyBytes
	ld a, [wUnlockedUnownMode]
	and a
	jr nz, .cursor
	ld hl, wPokedexWRAM0Scratch + 1
	dec [hl]
.cursor
	ld de, wPokedexWRAM0Scratch
	farcall Pokedex_MoveArrowCursor
	call c, PokedexListing_ModeDescription
	ldh a, [hJoyPressed]
	and PAD_SELECT | PAD_B
	jr nz, .return
	ldh a, [hJoyPressed]
	and PAD_A
	ret z
	call PokedexListing_GetModeID
	cp DEXMENU_UNOWN
	jr nc, .other
	ld hl, wPokedexListingPresentation
	cp [hl]
	jr z, .return
	ld [hl], a
	ld [wLastDexPresentation], a
	and a
	jr nz, .linear
	farcall Pokedex_InitGridCacheState
; A Legacy offset may not align to a three-column grid. Normalize from an
; empty saved viewport; the shared helper chooses a row containing selection.
	xor a
	ld [wPokedexListingSavedScrollOffset], a
	ld [wPokedexListingSavedScrollOffset + 1], a
	ld a, POKEDEX_GRID_SIZE
	ld [wDexListingHeight], a
	farcall Pokedex_NormalizeListingAfterSelectedMon
	jr .return
.linear
	ld a, POKEDEX_LEGACY_HEIGHT
	ld [wDexListingHeight], a
	farcall PokedexSelectedMon_NormalizeLinearReturn
	jr .return
.return
	call PokedexListing_BeginMenuTransition
	ld a, DEXSELECT_STATE_MENU_RETURN
	ld [wPokedexSelectedState], a
	ld a, DEXSTATE_MAIN_SCR
	ld [wJumptableIndex], a
	ret
.other
; Future modes can be highlighted without changing the Listing or its order.
	cp DEXMENU_UNOWN
	ret nz
	ld a, [wUnlockedUnownMode]
	and a
	ret z
.unown
	call PokedexListing_BeginMenuTransition
	ld a, DEXSTATE_UNOWN_MODE
	ld [wJumptableIndex], a
	ret
.Cursor:
	db PAD_UP | PAD_DOWN, 5
	dwcoord 2, 3
	dwcoord 2, 5
	dwcoord 2, 7
	dwcoord 2, 9
	dwcoord 2, 11

PokedexListing_GetModeID:
	ld a, [wUnlockedUnownMode]
	and a
	ld hl, .Locked
	jr z, .index
	ld hl, .Unlocked
.index
	ld a, [wDexArrowCursorPosIndex]
	ld e, a
	ld d, 0
	add hl, de
	ld a, [hl]
	ret
.Locked:
	db DEXMENU_MODERN, DEXMENU_LEGACY, DEXMENU_MOVES, DEXMENU_TYPES
.Unlocked:
	db DEXMENU_MODERN, DEXMENU_LEGACY, DEXMENU_UNOWN, DEXMENU_MOVES, DEXMENU_TYPES

PokedexListing_ModeDescription:
	xor a
	ldh [hBGMapMode], a
	hlcoord 0, 13
	lb bc, 3, 18
	call PokedexLegacy_PlaceBorder
	call PokedexListing_GetModeID
	ld hl, .Descriptions
	ld e, a
	ld d, 0
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld e, l
	ld d, h
	hlcoord 1, 14
	call PlaceString
	ld a, 1
	ldh [hBGMapMode], a
	ret
.Descriptions:
	dw .Modern, .Legacy, .Unown, .Moves, .Types
.Modern:
	db   "Displays <PK><MN> in a"
	next "visual grid.@"
.Legacy:
	db   "Displays <PK><MN> in the"
	next "classic text list.@"
.Unown:
	db   "Displays all Unown"
	next "forms caught.@"
.Moves:
	db   "Move descriptions"
	next "and stats.@"
.Types:
	db   "<PK><MN> Type weaknesses"
	next "and resistances.@"

PokedexLegacy_FillColumn:
	push de
	ld de, SCREEN_WIDTH
.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	pop de
	ret

PokedexLegacy_PlaceTiles:
.loop
	ld a, [de]
	cp -1
	ret z
	inc de
	ld [hli], a
	jr .loop

PokedexLegacy_PlaceBorder:
	push hl
	ld a, $33
	ld [hli], a
	ld d, $34
	call .FillRow
	ld [hl], $35
	pop hl
	ld de, SCREEN_WIDTH
	add hl, de
.loop
	push hl
	ld [hl], $36
	inc hl
	ld d, $7f
	call .FillRow
	ld [hl], $37
	pop hl
	ld de, SCREEN_WIDTH
	add hl, de
	dec b
	jr nz, .loop
	ld [hl], $38
	inc hl
	ld d, $39
	call .FillRow
	ld [hl], $3a
	ret
.FillRow
	ld e, c
.row_loop
	ld a, e
	and a
	ret z
	ld a, d
	ld [hli], a
	dec e
	jr .row_loop
