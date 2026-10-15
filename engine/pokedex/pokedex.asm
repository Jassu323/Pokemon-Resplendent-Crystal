; Pokedex_RunJumptable.Jumptable indexes
	const_def
	const DEXSTATE_MAIN_SCR
	const DEXSTATE_UPDATE_MAIN_SCR
	const DEXSTATE_SELECTED_MON_ENTER
	const DEXSTATE_SELECTED_MON_UPDATE
	const DEXSTATE_SELECTED_MON_RESERVED
	const DEXSTATE_SEARCH_SCR
	const DEXSTATE_UPDATE_SEARCH_SCR
	const DEXSTATE_OPTION_SCR
	const DEXSTATE_UPDATE_OPTION_SCR
	const DEXSTATE_SEARCH_RESULTS_SCR
	const DEXSTATE_UPDATE_SEARCH_RESULTS_SCR
	const DEXSTATE_UNOWN_MODE
	const DEXSTATE_UPDATE_UNOWN_MODE
	const DEXSTATE_EXIT
	const DEXSTATE_POPOVER
	const DEXSTATE_MOVES_MODE_INIT
	const DEXSTATE_MOVES_MODE_UPDATE
	const DEXSTATE_MOVES_MODE_SORT
	const DEXSTATE_MOVES_OPTIONS
	const DEXSTATE_MOVES_SEARCH
	const DEXSTATE_MOVES_TEXT_ENTRY
	const DEXSTATE_TYPES_INIT
	const DEXSTATE_TYPES_UPDATE

	const_def
	const DEXSELECT_VIEW_DESCRIPTION
	const DEXSELECT_VIEW_INFO
	const DEXSELECT_VIEW_MOVES
	const DEXSELECT_VIEW_AREA

	const_def
	const DEXSELECT_STATE_ENTERING
	const DEXSELECT_STATE_ACTIVE
	const DEXSELECT_STATE_SWITCHING_SPECIES
	const DEXSELECT_STATE_SWITCHING_VIEW
	const DEXSELECT_STATE_AREA_ACTIVE
	const DEXSELECT_STATE_LEAVING
	const DEXSELECT_STATE_MENU_RETURN
	const DEXSELECT_STATE_UNOWN_RETURN
	const DEXSELECT_STATE_MOVES_RETURN
	const DEXSELECT_STATE_TYPES_RETURN

	const_def
	const POKEDEX_OWNER_TRANSITION_NONE
	const POKEDEX_OWNER_TRANSITION_DESCRIPTION
	const POKEDEX_OWNER_TRANSITION_LISTING
	const POKEDEX_OWNER_TRANSITION_INTERNAL_DESCRIPTION
	const POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT
	const POKEDEX_OWNER_TRANSITION_INFO
	const POKEDEX_OWNER_TRANSITION_INFO_RETURN

	const_def
	const POKEDEX_DESCRIPTION_TEXT_IDLE
	const POKEDEX_DESCRIPTION_TEXT_INITIALIZE
	const POKEDEX_DESCRIPTION_TEXT_CATEGORY
	const POKEDEX_DESCRIPTION_TEXT_SKIP_PAGE
	const POKEDEX_DESCRIPTION_TEXT_RENDER
	const POKEDEX_DESCRIPTION_TEXT_BADGE

DEF POKEDEX_DESCRIPTION_TEXT_CHUNK EQU 24
DEF POKEDEX_DESCRIPTION_TEXT_SLICES EQU 3
DEF POKEDEX_DESCRIPTION_TEXT_LATEST_LY EQU 96

DEF POKEDEX_SELECTED_EXTENDED_BG_PALS EQU %11111100
DEF POKEDEX_LISTING_OBJ_PALS EQU %00111111

EXPORT DEF POKEDEX_SCX EQU 5

DEF POKEDEX_GRID_WIDTH  EQU 3
DEF POKEDEX_GRID_HEIGHT EQU 3
DEF POKEDEX_GRID_SIZE   EQU POKEDEX_GRID_WIDTH * POKEDEX_GRID_HEIGHT
DEF DEXLIST_MODERN EQU 0
DEF DEXLIST_LEGACY EQU 1
DEF POKEDEX_LEGACY_HEIGHT EQU 7
DEF POKEDEX_LEGACY_JUNCTION_TILE EQU $62
DEF POKEDEX_LEGACY_CAP_TILE EQU $63
DEF POKEDEX_LEGACY_DIVIDER_TILE EQU $64
DEF POKEDEX_LEGACY_ARROW_TILE EQU $7e
DEF POKEDEX_GRID_CACHE_ROWS EQU POKEDEX_GRID_HEIGHT + 2

DEF POKEDEX_GRID_SEEN_F   EQU 0
DEF POKEDEX_GRID_CAUGHT_F EQU 1

	const_def
	const POKEDEX_GRID_SCROLL_NONE
	const POKEDEX_GRID_SCROLL_UP
	const POKEDEX_GRID_SCROLL_DOWN
	const POKEDEX_GRID_SCROLL_WRAP_UP
	const POKEDEX_GRID_SCROLL_WRAP_DOWN

DEF POKEDEX_GRID_SCROLL_SELECTION_F EQU 0
DEF POKEDEX_GRID_SCROLL_COMMIT_F    EQU 1

DEF POKEDEX_SCROLLBAR_TILE     EQU $ba
DEF POKEDEX_UNSEEN_TILE        EQU $c6
DEF POKEDEX_SIDE_ICON_TILE     EQU $00
DEF POKEDEX_SIDE_ICON_FRAME1_TILE EQU $d2
DEF POKEDEX_SIDE_ICON_FRAME1_VRAM_TILE EQU $52
DEF POKEDEX_CENTER_ICON_TILE   EQU $00
DEF POKEDEX_LIST_CURSOR_TILE   EQU $40
DEF POKEDEX_CAUGHT_BALL_TILE   EQU $41
DEF POKEDEX_SCROLL_THUMB_TILE  EQU $0f
DEF POKEDEX_GFX_TILE_COUNT     EQU $40
DEF POKEDEX_JOINED_LEFT_TILE   EQU $54
DEF POKEDEX_JOINED_MIDDLE_TILE EQU $5b
DEF POKEDEX_RESIDENT_FOOTPRINT_TILE     EQU $b1
DEF POKEDEX_RESIDENT_UNOWN_FONT_TILE    EQU $b5
DEF POKEDEX_RESIDENT_JOINED_LEFT_TILE   EQU $d0
DEF POKEDEX_RESIDENT_JOINED_MIDDLE_TILE EQU $d1
DEF POKEDEX_DESCRIPTION_GFX_TILE EQU $71
DEF POKEDEX_DESCRIPTION_ALT_FOOTPRINT_TILE EQU $6c
DEF POKEDEX_DESCRIPTION_FOOTPRINT_PAL EQU 2
DEF POKEDEX_TYPE_OBJ_TILE EQU $28
DEF POKEDEX_INFO_MINI_OBJ_TILE EQU $38
DEF POKEDEX_INFO_HP_OBJ_TILE EQU $58
DEF POKEDEX_INFO_TILES EQU 40
DEF POKEDEX_INFO_SHARED_TILES EQU 15
DEF POKEDEX_INFO_SERVICE_SLICES EQU 3
; Leave room for a lower-panel slice, cry interrupts and the owner-loop refill.
DEF POKEDEX_INFO_LATEST_LY EQU 64
	const_def
	const POKEDEX_INFO_IDLE
	const POKEDEX_INFO_CLEAR
	const POKEDEX_INFO_PLAN
	const POKEDEX_INFO_COPY
	const POKEDEX_INFO_UPLOAD
	const POKEDEX_INFO_READY
	const POKEDEX_INFO_INITIALIZE
	const POKEDEX_INFO_MINI_UPLOAD
	const POKEDEX_INFO_RECORD
DEF POKEDEX_RENDER_KEY_UNSEEN  EQU -1

DEF POKEDEX_GRID_ICON_ANIM_FRAME_F EQU 3

DEF POKEDEX_ANIM_PAYLOAD       EQUS "wPokedexWRAM0Scratch"
DEF POKEDEX_ANIM_PLAN_BUFFER   EQUS "wPokedexWRAM0Scratch + $310"
DEF POKEDEX_ANIM_SLOT_A_MAP    EQUS "wPokedexWRAM0Scratch + $39c"
DEF POKEDEX_ANIM_SLOT_A_ATTRS  EQUS "wPokedexWRAM0Scratch + $3cd"
DEF POKEDEX_ANIM_SLOT_B_MAP    EQUS "wPokedexWRAM0Scratch + $3fe"
DEF POKEDEX_ANIM_SLOT_B_ATTRS  EQUS "wPokedexWRAM0Scratch + $42f"
DEF POKEDEX_ANIM_SOURCE_TILES  EQUS "wPokedexWRAM0Scratch + $460"

; Selection staging ends at $350. The animation producer is inactive while
; a Listing row is being changed, so its map workspace can stage both frames
; of one incoming icon row without reserving another persistent buffer.
DEF POKEDEX_GRID_CENTER_GFX     EQUS "wPokedexWRAM0Scratch + $350"
DEF POKEDEX_GRID_SIDE_FRAME0_GFX EQUS "wPokedexWRAM0Scratch + $3d0"
DEF POKEDEX_GRID_SIDE_FRAME1_GFX EQUS "wPokedexWRAM0Scratch + $450"

; Persistent for the full Pokedex session. This begins after both the
; animation workspace and the Listing's temporary icon-row staging.
DEF POKEDEX_ORDER_SEEN_FLAGS EQUS "wPokedexWRAM0Scratch + $4d0"
DEF POKEDEX_ORDER_SEEN_BYTES EQU (NUM_POKEMON + 7) / 8

; Persistent icon destination, outside even the maximum 512-species bitset.
DEF POKEDEX_DESCRIPTION_ICON_BUFFER EQUS "wPokedexWRAM0ScratchEnd - 1"
ASSERT POKEDEX_DESCRIPTION_ICON_BUFFER >= wPokedexWRAM0Scratch + $510
ASSERT POKEDEX_ORDER_SEEN_FLAGS + POKEDEX_ORDER_SEEN_BYTES <= POKEDEX_DESCRIPTION_ICON_BUFFER

DEF POKEDEX_ANIM_BUFFER_A_TILE EQU $80
DEF POKEDEX_ANIM_BUFFER_B_TILE EQU $33

DEF POKEDEX_ANIM_ACTIVE_F       EQU 0
DEF POKEDEX_ANIM_TIMELINE_READY_F EQU 1
DEF POKEDEX_ANIM_STAGE_VALID_F  EQU 2
DEF POKEDEX_ANIM_STAGE_READY_F  EQU 3
DEF POKEDEX_ANIM_ENDED_F        EQU 4
DEF POKEDEX_ANIM_MAP_PENDING_F  EQU 5
DEF POKEDEX_ANIM_MAP_PUBLISHED_F EQU 6
DEF POKEDEX_ANIM_FIRST_PUBLICATION_F EQU 7

DEF POKEDEX_ANIM_UPLOAD_CHUNK_TILES EQU 20
DEF POKEDEX_ANIM_STARTUP_STREAMS     EQU 16
DEF POKEDEX_ANIM_STARTUP_TILES EQU POKEDEX_ANIM_STARTUP_STREAMS * FRONTPIC_ANIM_DICTIONARY_CHUNK_TILES

DEF POKEDEX_ANIM_PLAYBACK_INACTIVE EQU 0
DEF POKEDEX_ANIM_PLAYBACK_WAITING  EQU 1
DEF POKEDEX_ANIM_PLAYBACK_PLAYING  EQU 2
DEF POKEDEX_ANIM_PLAYBACK_DONE     EQU 3

DEF POKEDEX_ANIM_TIMELINE_FINISH EQU $f0
DEF POKEDEX_ANIM_TIMELINE_LOOP   EQU $f1

DEF POKEDEX_ANIM_WORK_DECODE EQU $40
DEF POKEDEX_ANIM_WORK_UPLOAD EQU $c0
DEF POKEDEX_ANIM_AUDIO_DUE_F EQU 0
DEF POKEDEX_ANIM_FINISH_USED_F EQU 1
DEF POKEDEX_ANIM_UPLOAD_ACTIVE_F EQU 2
DEF POKEDEX_ANIM_STAGE_WORK_MASK EQU $7c

Pokedex:
	ldh a, [hWX]
	ld l, a
	ldh a, [hWY]
	ld h, a
	push hl
	ldh a, [hSCX]
	push af
	ld hl, wOptions
	ld a, [hl]
	push af
	set NO_TEXT_SCROLL, [hl]
	ld a, [wStateFlags]
	push af
	xor a
	ld [wStateFlags], a
	ldh a, [hInMenu]
	push af
	ld a, $1
	ldh [hInMenu], a

	xor a
	ldh [hMapAnims], a
	call InitPokedex
	call DelayFrame

.main
	farcall Pokedex_BeginOwnerLoop
	ld a, [wJumptableIndex]
	bit JUMPTABLE_EXIT_F, a
	jr nz, .exit
	call Pokedex_RunJumptable
	farcall Pokedex_EndOwnerLoop
	jr .main

.exit
	ld de, SFX_READ_TEXT_2
	call PlaySFX
	call WaitSFX
	call ClearSprites
	; Publish white before the map reload disables VBlank palette updates.
	call ClearPalettes
	call DelayFrame
	ld a, [wCurDexMode]
	ld [wLastDexMode], a
	ld a, [wPokedexListingPresentation]
	ld [wLastDexPresentation], a
	call Pokedex_ClearLockedIDs

	pop af
	ldh [hInMenu], a
	pop af
	ld [wStateFlags], a
	pop af
	ld [wOptions], a
	pop af
	ldh [hSCX], a
	pop hl
	ld a, l
	ldh [hWX], a
	ld a, h
	ldh [hWY], a
	ret

InitPokedex:
	call ClearPalettes
	call ClearSprites
	call Pokedex_LoadGFX
	call ClearTilemap

	ld hl, wPokedexDataStart
	ld bc, wPokedexDataEnd - wPokedexDataStart
	xor a
	call ByteFill
	ld a, -1
	ld [wPokedexResidentFootprintSpecies], a

	xor a
	ld [wJumptableIndex], a
	ld [wPrevDexEntryJumptableIndex], a
	ld [wPrevDexEntryBackup], a
	ld [wPrevDexEntryBackup + 1], a

	call Pokedex_CheckUnlockedUnownMode

	ld a, [wLastDexMode]
	ld [wCurDexMode], a
	ld a, [wLastDexPresentation]
	cp DEXLIST_LEGACY + 1
	jr c, .presentation_valid
	xor a
.presentation_valid
	ld [wPokedexListingPresentation], a

	farcall Pokedex_OrderMonsByMode
	farcall Pokedex_InitListingPresentation
	call Pokedex_RestoreListingPosition
	ld a, [wPokedexListingPresentation]
	and a
	jr nz, .grid_cache_ready
	ldh a, [hCGB]
	and a
	jr z, .grid_cache_ready
	farcall Pokedex_EnsureGridCache
.grid_cache_ready
	call Pokedex_GetLandmark
	farcall Pokedex_InitListingRightEdge
	call Pokedex_ResetBGMapMode
	; fallthrough

Pokedex_ClearLockedIDs:
	xor a
	ld l, LOCKED_MON_ID_DEX_SELECTED
	jp LockPokemonID

Pokedex_CheckUnlockedUnownMode:
	ld a, [wStatusFlags]
	bit STATUSFLAGS_UNOWN_DEX_F, a
	jr nz, .unlocked

	xor a
	ld [wUnlockedUnownMode], a
	ret

.unlocked
	ld a, TRUE
	ld [wUnlockedUnownMode], a
	ret

Pokedex_InitGridCursorPosition:
	xor a
	ld [wDexListingScrollOffset], a
	ld [wDexListingScrollOffset + 1], a
	ld [wDexListingCursor], a
	ld [wPokedexGridScrollDirection], a
	ld [wPokedexGridScrollFlags], a
	farcall Pokedex_InitGridCacheState
	ld a, POKEDEX_GRID_SIZE
	ld [wDexListingHeight], a
	ret

Pokedex_SaveListingViewport:
	ld a, [wDexListingScrollOffset]
	ld [wPokedexListingSavedScrollOffset], a
	ld a, [wDexListingScrollOffset + 1]
	ld [wPokedexListingSavedScrollOffset + 1], a
	ret

INCLUDE "engine/pokedex/pokedex_position.asm"

Pokedex_GetLandmark:
	ld a, [wMapGroup]
	ld b, a
	ld a, [wMapNumber]
	ld c, a
	call GetWorldMapLocation

	cp LANDMARK_SPECIAL
	jr nz, .load

	ld a, [wBackupMapGroup]
	ld b, a
	ld a, [wBackupMapNumber]
	ld c, a
	call GetWorldMapLocation

.load
	ld [wDexCurLocation], a
	ret

Pokedex_RunJumptable:
	ld a, [wJumptableIndex]
	ld hl, .Jumptable
	call Pokedex_LoadPointer
	jp hl

.Jumptable:
; entries correspond to DEXSTATE_* constants
	dw Pokedex_InitMainScreen
	dw Pokedex_UpdateMainScreen
	dw Pokedex_InitSelectedMon
	dw Pokedex_UpdateSelectedMon
	dw Pokedex_UpdateSelectedMon
	dw Pokedex_InitSearchScreen
	dw Pokedex_UpdateSearchScreen
	dw Pokedex_InitOptionScreen
	dw Pokedex_UpdateOptionScreen
	dw Pokedex_InitSearchResultsScreen
	dw Pokedex_UpdateSearchResultsScreen
	dw Pokedex_InitUnownMode
	dw Pokedex_UpdateUnownMode
	dw Pokedex_Exit
	dw Pokedex_UpdatePopover
	dw Pokedex_InitMovesMode
	dw Pokedex_UpdateMovesMode
	dw Pokedex_UpdateMovesModeSort
	dw Pokedex_UpdateMovesOptions
	dw Pokedex_UpdateMovesSearch
	dw Pokedex_UpdateMovesTextEntry
	dw Pokedex_InitTypes
	dw Pokedex_UpdateTypes

Pokedex_InitTypes:
	farcall PokedexTypes_Initialize
	ret
Pokedex_UpdateTypes:
	farcall PokedexTypes_Update
	ret

Pokedex_InitMovesMode:
	farcall PokedexMovesMode_Initialize
	ret
Pokedex_UpdateMovesMode:
	farcall PokedexMovesMode_Update
	ret
Pokedex_UpdateMovesModeSort:
	farcall PokedexMovesMode_SortUpdate
	ret

Pokedex_UpdateMovesOptions:
	farcall PokedexMovesSearch_OptionsUpdate
	ret
Pokedex_UpdateMovesSearch:
	farcall PokedexMovesSearch_Update
	ret
Pokedex_UpdateMovesTextEntry:
	farcall PokedexMovesSearch_TextUpdate
	ret

Pokedex_UpdatePopover:
	farcall PokedexPopover_Update
	ret

Pokedex_IncrementDexPointer:
	ld hl, wJumptableIndex
	inc [hl]
	ret

Pokedex_Exit:
	xor a
	ldh [hVBlank], a
	ld hl, wJumptableIndex
	set JUMPTABLE_EXIT_F, [hl]
	ret

Pokedex_InitMainScreen:
	ld a, [wPokedexListingPresentation]
	and a
	jr z, .modern
	farcall PokedexLegacy_InitMainScreen
	ret
.modern
	xor a
	ldh [hVBlank], a
	ldh [hBGMapMode], a
	ld [wPokedexGridIconAnimFrame], a
	ld a, TRUE
	ldh [hOAMUpdate], a
	ldh a, [hCGB]
	and a
	jr z, .stage_listing
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_LEAVING
	jr z, .stage_listing
	cp DEXSELECT_STATE_MENU_RETURN
	jr z, .stage_listing
	ld a, $a7
	ldh [hWX], a
	call ClearPalettes
	call DelayFrame
.stage_listing
	call ClearSprites
	call Pokedex_LoadListJoinedBorderGFX
	ldh a, [hCGB]
	and a
	jr z, .cache_ready
	farcall Pokedex_EnsureGridCache
.cache_ready
	call Pokedex_LoadGridPage
	farcall DrawPokedexListWindow
	call Pokedex_PrintSelectedName
	hlcoord 0, 17
	ld de, String_START_OPTION
	call Pokedex_PlaceString
	ldh a, [hCGB]
	and a
	jr z, .copy_dmg_window
	farcall Pokedex_CopyBackingToWindow
	jr .window_staged
.copy_dmg_window
	call Pokedex_SetBGMapMode3
.window_staged
	call Pokedex_ResetBGMapMode
	call Pokedex_DrawMainScreenBG
	ld a, POKEDEX_SCX
	ldh [hSCX], a
	xor a
	ldh [hWY], a
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_LEAVING
	jr z, .selected_tiles_ready
	ldh a, [hCGB]
	and a
	jr z, .load_selected_tiles
	farcall Pokedex_PrepareAndCommitSelectedMonGFX
	jr .selected_tiles_ready

.load_selected_tiles
	call Pokedex_LoadSelectedMonTiles
.selected_tiles_ready
	ldh a, [hCGB]
	and a
	jr z, .sgb_layout
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_LEAVING
	jr z, .stage_return_layout
	cp DEXSELECT_STATE_MENU_RETURN
	jr nz, .cgb_cold_layout
.stage_return_layout
	farcall CGB_PokedexStageListLayout
	jr .layout_ready

.cgb_cold_layout
	farcall CGB_PokedexStageListLayout
	jr .layout_ready

.sgb_layout
	ld a, SCGB_POKEDEX
	call Pokedex_GetSGBLayout
.layout_ready
	xor a
	ldh [hBGMapMode], a
	ldh a, [hCGB]
	and a
	jr z, .copy_dmg_bg
	xor a
	ldh [hCGBPalUpdate], a
	farcall Pokedex_PublishOrStageListingBacking
	jr .bg_staged
.copy_dmg_bg
	call WaitBGMap
	call Pokedex_ResetBGMapMode
.bg_staged
	call Pokedex_RecordRenderedSelectionKey
	farcall Pokedex_UpdateGridOAM
	farcall DrawPokedexListWindow
	call Pokedex_PrintSelectedName
	hlcoord 0, 17
	ld de, String_START_OPTION
	call Pokedex_PlaceString
	ldh a, [hCGB]
	and a
	jr z, .reveal_dmg
	farcall Pokedex_RevealOrCommitListing
	jr .revealed
.reveal_dmg
	ld a, $47
	ldh [hWX], a
	xor a
	ldh [hOAMUpdate], a
.revealed
	ldh a, [hCGB]
	and a
	jr z, .handler_ready
	ld a, VBLANK_POKEDEX
	ldh [hVBlank], a
.handler_ready
	xor a
	ld [wPokedexSelectedState], a
	call Pokedex_IncrementDexPointer
	ret

Pokedex_UpdateMainScreen:
	ld hl, hJoyPressed
	ld a, [hl]
	and PAD_B
	jp nz, .b
	ld a, [hl]
	and PAD_A
	jp nz, .a
	ld a, [hl]
	and PAD_SELECT
	jp nz, .select
	ld a, [hl]
	and PAD_START
	jp nz, .start
	ld a, [wPokedexListingPresentation]
	and a
	jr z, .modern
	farcall PokedexLegacy_UpdateMainScreen
	ret
.modern
	call Pokedex_GridHandleDPadInput
	jr c, .selection_changed
	ret
.selection_changed
	ld a, [wPokedexGridScrollDirection]
	cp POKEDEX_GRID_SCROLL_WRAP_UP
	jp nc, .grid_wrapped
	and a
	jr nz, .grid_scrolled
	call Pokedex_GetSelectionRenderKey
	ld hl, wPokedexRenderedSelectionKey
	cp [hl]
	jr z, .update_cursor
	farcall Pokedex_CancelAnimationPrefetch
	ldh a, [hCGB]
	and a
	jr z, .dmg_selection
	xor a
	ldh [hBGMapMode], a
	call Pokedex_PrintSelectedName
	call Pokedex_PrepareSelectedMonTiles
	farcall CGB_PokedexPrepareFrontpicPalette
	farcall Pokedex_CommitStagedSelection
	farcall CGB_PokedexCommitFrontpicPalette
	ld a, TRUE
	ldh [hOAMUpdate], a
	farcall Pokedex_SyncGridIconAnimationFrame
	farcall Pokedex_UpdateGridCursorOAM
	farcall Pokedex_StageGridIconAnimation
	farcall Pokedex_CommitGridIconAnimationFrame
	xor a
	ldh [hOAMUpdate], a
	call Pokedex_RecordRenderedSelectionKey
	ret

.dmg_selection
	xor a
	ldh [hBGMapMode], a
	call Pokedex_PrintSelectedName
	call Pokedex_LoadSelectedMonTiles
	call Pokedex_SetBGMapMode3
	call Pokedex_ResetBGMapMode
	ld a, SCGB_POKEDEX
	call Pokedex_GetSGBLayout
	call Pokedex_RecordRenderedSelectionKey
.update_cursor
	farcall Pokedex_UpdateGridCursorOAM
	ret

.grid_scrolled
	farcall Pokedex_UpdateScrolledGrid
	ret

.grid_wrapped
	farcall Pokedex_UpdateWrappedGrid
	ret

.a
	call Pokedex_GetSelectedMon
	call Pokedex_CheckSeen
	ret z
	call Pokedex_StopGridIconAnimation
	call Pokedex_SaveListingViewport
	ld a, DEXSTATE_SELECTED_MON_ENTER
	ld [wJumptableIndex], a
	ld a, DEXSTATE_MAIN_SCR
	ld [wPrevDexEntryJumptableIndex], a
	ret

.select
	farcall Pokedex_CancelAnimationPrefetch
	call Pokedex_GetSelectedMon
	call Pokedex_SaveListingViewport
	farcall PokedexSelectedMon_CaptureListingSelection
	call Pokedex_StopGridIconAnimation
	farcall PokedexListing_BeginMenuTransition
	ld a, DEXSTATE_OPTION_SCR
	ld [wJumptableIndex], a
	ret

.start
	farcall PokedexPopover_Open
	ret

.b
	call Pokedex_RememberListingPosition
	call Pokedex_StopGridIconAnimation
	ld a, DEXSTATE_EXIT
	ld [wJumptableIndex], a
	ret

Pokedex_StopGridIconAnimation:
	xor a
	ldh [hVBlank], a
	ret

Pokedex_InitSelectedMon:
	farcall PokedexSelectedMon_Enter
	ret

Pokedex_UpdateSelectedMon:
	farcall PokedexSelectedMon_Update
	ret

PokedexSelectedMon_ReadFooterCursor:
	ld de, DexEntryScreen_ArrowCursorData
	jp Pokedex_MoveArrowCursor

DexEntryScreen_ArrowCursorData:
	db PAD_RIGHT | PAD_LEFT, 4
	dwcoord 1, 17  ; DESC
	dwcoord 6, 17  ; STAT
	dwcoord 11, 17 ; MOV
	dwcoord 15, 17 ; AREA

Pokedex_InitOptionScreen:
	farcall PokedexListing_InitModeScreen
	ret

Pokedex_UpdateOptionScreen:
	farcall PokedexListing_UpdateModeScreen
	ret

Pokedex_InitSearchScreen:
	farcall PokedexSearch_Initialize
	xor a
	ldh [hBGMapMode], a
	call ClearSprites
	call Pokedex_DrawSearchScreenBG
	call Pokedex_InitArrowCursor
	ld a, 1 ; Bug starts the alphabetical selector
	ld [wDexSearchMonType1], a
	xor a
	ld [wDexSearchMonType2], a
	call Pokedex_PlaceSearchScreenTypeStrings
	xor a
	ld [wDexSearchSlowpokeFrame], a
	farcall DoDexSearchSlowpokeFrame
	call WaitBGMap
	ld a, SCGB_POKEDEX_SEARCH_OPTION
	call Pokedex_GetSGBLayout
	farcall PokedexListing_RevealMenu
	call Pokedex_IncrementDexPointer
	ret

Pokedex_UpdateSearchScreen:
	ld de, .ArrowCursorData
	call Pokedex_MoveArrowCursor
	call Pokedex_UpdateSearchMonType
	call c, Pokedex_PlaceSearchScreenTypeStrings
	ld hl, hJoyPressed
	ld a, [hl]
	and PAD_START | PAD_B
	jr nz, .cancel
	ld a, [hl]
	and PAD_A
	jr nz, .do_menu_action
	ret

.do_menu_action
	ld a, [wDexArrowCursorPosIndex]
	ld hl, .MenuActionJumptable
	call Pokedex_LoadPointer
	jp hl

.cancel
	farcall PokedexSearch_Leave
	farcall PokedexListing_BeginMenuTransition
	ld a, DEXSTATE_MAIN_SCR
	ld [wJumptableIndex], a
	ret

.ArrowCursorData:
	db PAD_UP | PAD_DOWN, 4
	dwcoord 1, 4  ; TYPE 1
	dwcoord 1, 6  ; TYPE 2
	dwcoord 2, 13 ; BEGIN SEARCH
	dwcoord 2, 15 ; CANCEL

.MenuActionJumptable:
	dw .MenuAction_MonSearchType
	dw .MenuAction_MonSearchType
	dw .MenuAction_BeginSearch
	dw .MenuAction_Cancel

.MenuAction_MonSearchType:
	call Pokedex_NextSearchMonType
	call Pokedex_PlaceSearchScreenTypeStrings
	ret

.MenuAction_BeginSearch:
	call Pokedex_SearchForMons
	farcall AnimateDexSearchSlowpoke
	ld hl, wDexSearchResultCount
	ld a, [hli]
	or [hl]
	jr nz, .show_search_results

; No mon with matching types was found.
	farcall Pokedex_OrderMonsByMode
	call Pokedex_DisplayTypeNotFoundMessage
	xor a
	ldh [hBGMapMode], a
	call Pokedex_DrawSearchScreenBG
	call Pokedex_InitArrowCursor
	call Pokedex_PlaceSearchScreenTypeStrings
	call WaitBGMap
	ret

.show_search_results
	ld a, [wDexSearchResultCount]
	ld [wDexListingEnd], a
	ld a, [wDexSearchResultCount + 1]
	ld [wDexListingEnd + 1], a
	ld a, [wDexListingScrollOffset]
	ld [wDexListingScrollOffsetBackup], a
	ld a, [wDexListingScrollOffset + 1]
	ld [wDexListingScrollOffsetBackup + 1], a
	ld a, [wDexListingCursor]
	ld [wDexListingCursorBackup], a
	ld a, [wPrevDexEntry]
	ld [wPrevDexEntryBackup], a
	ld a, [wPrevDexEntry + 1]
	ld [wPrevDexEntryBackup + 1], a
	xor a
	ld [wDexListingScrollOffset], a
	ld [wDexListingScrollOffset + 1], a
	ld [wDexListingCursor], a
	farcall PokedexSearch_Leave
	farcall PokedexListing_BeginMenuTransition
	ld a, DEXSTATE_SEARCH_RESULTS_SCR
	ld [wJumptableIndex], a
	ret

.MenuAction_Cancel:
	farcall PokedexSearch_Leave
	farcall PokedexListing_BeginMenuTransition
	ld a, DEXSTATE_MAIN_SCR
	ld [wJumptableIndex], a
	ret

Pokedex_InitSearchResultsScreen:
	farcall PokedexResults_Initialize
	jp Pokedex_IncrementDexPointer

Pokedex_UpdateSearchResultsScreen:
	ld hl, hJoyPressed
	ld a, [hl]
	and PAD_B
	jr nz, .return_to_search_screen
	ld a, [hl]
	and PAD_A
	jr nz, .go_to_dex_entry
	call Pokedex_ListingHandleDPadInput
	ret nc
	farcall PokedexResults_Scroll
	ret

.go_to_dex_entry
	call Pokedex_GetSelectedMon
	call Pokedex_CheckSeen
	ret z
	ld a, DEXSTATE_SELECTED_MON_ENTER
	ld [wJumptableIndex], a
	ld a, DEXSTATE_SEARCH_RESULTS_SCR
	ld [wPrevDexEntryJumptableIndex], a
	ret

.return_to_search_screen
	ld a, [wDexListingScrollOffsetBackup]
	ld [wDexListingScrollOffset], a
	ld a, [wDexListingScrollOffsetBackup + 1]
	ld [wDexListingScrollOffset + 1], a
	ld a, [wDexListingCursorBackup]
	ld [wDexListingCursor], a
	ld a, [wPrevDexEntryBackup]
	ld [wPrevDexEntry], a
	ld a, [wPrevDexEntryBackup + 1]
	ld [wPrevDexEntry + 1], a
	farcall PokedexListing_BeginMenuTransition
	farcall Pokedex_OrderMonsByMode
	ld a, DEXSTATE_SEARCH_SCR
	ld [wJumptableIndex], a
	xor a
	ldh [hSCX], a
	ld a, $a7
	ldh [hWX], a
	ret

Pokedex_InitUnownMode:
	ldh a, [hCGB]
	and a
	jr z, .ordinary_font
	farcall PokedexAncestors_RestoreUnownFont
	jr .font_ready
.ordinary_font
	call Pokedex_LoadUnownFont
.font_ready
	call Pokedex_DrawUnownModeBG
	xor a
	ld [wDexCurUnownIndex], a
	call Pokedex_LoadUnownFrontpicTiles
	call Pokedex_UnownModePlaceCursor
	farcall PrintUnownWord
	ldh a, [hCGB]
	and a
	jr z, .mapped
	farcall PokedexUnown_Publish
	farcall PokedexUnown_PrepareLayout
	ld de, vBGMap0
	farcall PokedexPerf_FastTownMap
	call Pokedex_ApplyUsualPals
	jr .reveal
.mapped
	call WaitBGMap
	ld a, SCGB_POKEDEX_UNOWN_MODE
	call Pokedex_GetSGBLayout
.reveal
	farcall PokedexListing_RevealMenu
	call Pokedex_IncrementDexPointer
	ret

Pokedex_UpdateUnownMode:
	ld hl, hJoyPressed
	ld a, [hl]
	and PAD_A | PAD_B
	jr nz, .a_b
	call Pokedex_UnownModeHandleDPadInput
	ret

.a_b
	farcall PokedexListing_BeginMenuTransition
	ld a, DEXSELECT_STATE_UNOWN_RETURN
	ld [wPokedexSelectedState], a
	ld a, DEXSTATE_OPTION_SCR
	ld [wJumptableIndex], a
.done
	ret

Pokedex_UnownModeHandleDPadInput:
	ld hl, hJoyLast
	ld a, [hl]
	and PAD_RIGHT
	jr nz, .right
	ld a, [hl]
	and PAD_LEFT
	jr nz, .left
	ret

.right
	ld a, [wDexUnownCount]
	ld e, a
	ld hl, wDexCurUnownIndex
	ld a, [hl]
	inc a
	cp e
	ret nc
	ld a, [hl]
	inc [hl]
	jr .update

.left
	ld hl, wDexCurUnownIndex
	ld a, [hl]
	and a
	ret z
	ld a, [hl]
	dec [hl]

.update
	push af
	xor a
	ldh [hBGMapMode], a
	pop af
	call Pokedex_UnownModeEraseCursor
	call Pokedex_LoadUnownFrontpicTiles
	call Pokedex_UnownModePlaceCursor
	farcall PrintUnownWord
	ldh a, [hCGB]
	and a
	jr z, .dmg
	farcall PokedexUnown_Publish
	ret

.dmg
	ld a, $1
	ldh [hBGMapMode], a
	call DelayFrame
	call DelayFrame
	ret

Pokedex_UnownModeEraseCursor:
	ld c, ' '
	push af
	ldh a, [hCGB]
	and a
	jr z, .got_tile
	ld c, $32
.got_tile
	pop af
	jr Pokedex_UnownModeUpdateCursorGfx

Pokedex_UnownModePlaceCursor:
	ld c, FIRST_UNOWN_CHAR + NUM_UNOWN ; diamond cursor
	ldh a, [hCGB]
	and a
	jr z, .got_tile
	ld c, POKEDEX_RESIDENT_UNOWN_FONT_TILE + NUM_UNOWN
.got_tile
	ld a, [wDexCurUnownIndex]

Pokedex_UnownModeUpdateCursorGfx:
	ld e, a
	ld d, 0
	ld hl, UnownModeLetterAndCursorCoords + 2
rept 4
	add hl, de
endr
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld [hl], c
	ret

Pokedex_LoadListingScrollParams:
	; d = min(wDexListingEnd, wDexListingHeight); e = remaining scroll distance (cap at $FF)
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	cpl
	ld e, a
	ld a, [hli]
	cpl
	ld d, a
	inc hl
	; hl = wDexListingEnd
	ld a, [hli]
	ld h, [hl]
	ld l, a
	add hl, de
	inc hl
	ld a, [wDexListingHeight]
	ld d, a
	ld a, l
	sub d
	ld e, a
	ld a, h
	jr nc, .check_overflow
	sub 1
	jr c, .underflow
.check_overflow
	and a
	ret z
	ld e, $FF
	ret

.underflow
	ld e, h ; h = 0 here
	ld a, [wDexListingEnd]
	ld d, a
	ret

Pokedex_GridHandleDPadInput:
	xor a
	ld [wPokedexGridScrollDirection], a
	ld a, [wDexListingCursor]
	ld b, a
	ld hl, hJoyLast
	bit B_PAD_UP, [hl]
	jr nz, .up
	bit B_PAD_DOWN, [hl]
	jr nz, .down
	bit B_PAD_LEFT, [hl]
	jr nz, .left
	bit B_PAD_RIGHT, [hl]
	jr nz, .right
	jr .no_move

.up
	ld a, b
	cp POKEDEX_GRID_WIDTH
	jr c, .scroll_up
	sub POKEDEX_GRID_WIDTH
	jr .try_target

.scroll_up
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	or [hl]
	jr z, .wrap_up
	call Pokedex_ScrollGridUp
	scf
	ret

.wrap_up
	farcall Pokedex_WrapGridToBottom
	ret

.down
	; Test the absolute entry first. This also detects a partial final row,
	; where the cursor may not yet occupy the bottom local grid row.
	ld e, b
	ld d, 0
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a
	add hl, de
	ld de, POKEDEX_GRID_WIDTH
	add hl, de
	ld a, [wDexListingEnd]
	ld e, a
	ld a, [wDexListingEnd + 1]
	ld d, a
	ld a, l
	sub e
	ld a, h
	sbc d
	jr nc, .wrap_down
	ld a, b
	cp POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH
	jr nc, .scroll_down
	add POKEDEX_GRID_WIDTH
	jr .try_target

.scroll_down
	call Pokedex_ScrollGridDown
	scf
	ret

.wrap_down
	farcall Pokedex_WrapGridToTop
	ret

.left
	ld a, b
	and a
	jr z, .no_move
	cp POKEDEX_GRID_WIDTH
	jr z, .no_move
	cp 2 * POKEDEX_GRID_WIDTH
	jr z, .no_move
	dec a
	jr .try_target

.right
	ld a, b
	cp POKEDEX_GRID_WIDTH - 1
	jr z, .no_move
	cp 2 * POKEDEX_GRID_WIDTH - 1
	jr z, .no_move
	cp POKEDEX_GRID_SIZE - 1
	jr z, .no_move
	inc a

.try_target
	ld e, a
	ld d, 0
	ld hl, wPokedexGridOccupied
	add hl, de
	ld a, [hl]
	and a
	jr z, .no_move
	ld a, e
	ld [wDexListingCursor], a
	scf
	ret

.no_move
	and a
	ret

Pokedex_ScrollGridUp:
	ld a, TRUE
	ldh [hOAMUpdate], a
	ld hl, wDexListingScrollOffset
	ld a, [hl]
	sub POKEDEX_GRID_WIDTH
	ld [hli], a
	jr nc, .got_offset
	dec [hl]
.got_offset
	ld hl, wPokedexGridTopPhysicalRow
	ld a, [hl]
	and a
	jr nz, .decrement_physical_row
	ld a, POKEDEX_GRID_CACHE_ROWS
.decrement_physical_row
	dec a
	ld [hl], a
	call Pokedex_ShiftGridMetadataDown
	xor a
	call Pokedex_CacheGridRow
	ld a, POKEDEX_GRID_SCROLL_UP
	ld [wPokedexGridScrollDirection], a
	ret

Pokedex_ScrollGridDown:
	ld a, TRUE
	ldh [hOAMUpdate], a
	ld hl, wDexListingScrollOffset
	ld a, [hl]
	add POKEDEX_GRID_WIDTH
	ld [hli], a
	jr nc, .got_offset
	inc [hl]
.got_offset
	ld hl, wPokedexGridTopPhysicalRow
	ld a, [hl]
	inc a
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .got_physical_row
	xor a
.got_physical_row
	ld [hl], a
	call Pokedex_ShiftGridMetadataUp
	ld a, POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH
	call Pokedex_CacheGridRow
	ld a, POKEDEX_GRID_SCROLL_DOWN
	ld [wPokedexGridScrollDirection], a
	ret

Pokedex_ShiftGridMetadataUp:
; The old middle and bottom rows become the new top and middle rows.
	ld hl, wPokedexGridOccupied + POKEDEX_GRID_WIDTH
	ld de, wPokedexGridOccupied
	ld bc, POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH
	call CopyBytes
	ld hl, wPokedexGridFlags + POKEDEX_GRID_WIDTH
	ld de, wPokedexGridFlags
	ld bc, POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH
	call CopyBytes
	ld hl, wPokedexGridIconPalettes + POKEDEX_GRID_WIDTH
	ld de, wPokedexGridIconPalettes
	ld bc, POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH
	jp CopyBytes

Pokedex_ShiftGridMetadataDown:
; Copy backwards so the old top and middle rows become the new middle and
; bottom rows without clobbering their source entries.
	ld hl, wPokedexGridOccupied + POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH - 1
	ld de, wPokedexGridOccupied + POKEDEX_GRID_SIZE - 1
	call .CopyArrayBackward
	ld hl, wPokedexGridFlags + POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH - 1
	ld de, wPokedexGridFlags + POKEDEX_GRID_SIZE - 1
	call .CopyArrayBackward
	ld hl, wPokedexGridIconPalettes + POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH - 1
	ld de, wPokedexGridIconPalettes + POKEDEX_GRID_SIZE - 1
	; fallthrough

.CopyArrayBackward:
	ld c, POKEDEX_GRID_SIZE - POKEDEX_GRID_WIDTH
.loop
	ld a, [hld]
	ld [de], a
	dec de
	dec c
	jr nz, .loop
	ret

Pokedex_CacheGridRow:
; a = first visible grid position in the incoming row.
	ld [wDexTempCounter], a
	ld b, POKEDEX_GRID_WIDTH
.loop
	push bc
	ld a, [wDexTempCounter]
	push af
	call Pokedex_CacheGridPosition
	pop af
	inc a
	ld [wDexTempCounter], a
	pop bc
	dec b
	jr nz, .loop
	ret

Pokedex_ListingHandleDPadInput:
; Handles D-pad input for a list of Pokémon.
	call Pokedex_LoadListingScrollParams
	ld hl, hJoyLast
	bit B_PAD_UP, [hl]
	jr nz, Pokedex_ListingMoveCursorUp
	bit B_PAD_DOWN, [hl]
	jr nz, Pokedex_ListingMoveCursorDown
	ld a, [wDexListingHeight]
	xor d ; compares for equality (if zero) and clears carry
	ret nz
	bit B_PAD_LEFT, [hl]
	jr nz, Pokedex_ListingMoveUpOnePage
	bit B_PAD_RIGHT, [hl]
	jr nz, Pokedex_ListingMoveDownOnePage
	ret

Pokedex_ListingMoveCursorUp:
	ld hl, wDexListingCursor
	ld a, [hl]
	and a
	jr z, .try_scrolling
	dec [hl]
.done
	scf
	ret

.try_scrolling
	ld hl, wDexListingScrollOffset + 1
	ld a, [hld]
	and a
	ld a, [hl]
	jr nz, .go
	and a
	ret z
.go
	sub 1
	ld [hli], a
	jr nc, .done
	dec [hl]
	ret

Pokedex_ListingMoveCursorDown:
	ld hl, wDexListingCursor
	inc [hl]
	ld a, [hl]
	cp d
	ret c
	dec [hl]
	ld a, e
	and a
	ret z
	ld hl, wDexListingScrollOffset
	inc [hl]
	jr nz, .done
	inc hl
	inc [hl]
.done
	scf
	ret

Pokedex_ListingMoveUpOnePage:
	ld hl, wDexListingScrollOffset + 1
	ld a, [hld]
	or [hl]
	ret z
	ld a, [hl]
	sub d
	ld [hli], a
	jr nc, .done
	ld a, [hl]
	dec [hl]
	and a
	jr nz, .done
	; a = 0 here
	ld [hld], a
	ld [hl], a
.done
	scf
	ret

Pokedex_ListingMoveDownOnePage:
	ld a, e
	and a
	ret z
	cp d
	jr c, .got_scroll
	ld a, d
.got_scroll
	ld hl, wDexListingScrollOffset
	add a, [hl]
	ld [hli], a
	jr nc, .done
	inc [hl]
.done
	scf
	ret

Pokedex_FillColumn:
; Fills a column starting at hl, going downwards.
; b is the height of the column, and a is the tile it's filled with.
	push de
	ld de, SCREEN_WIDTH
.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	pop de
	ret

Pokedex_PrintLittleEndian:
	; in: hl, de as per PrintNum - bc will be set internally
	ld a, [de]
	ld [wPokedexDisplayNumber + 1], a
	inc de
	ld a, [de]
	ld de, wPokedexDisplayNumber
	ld [de], a
	lb bc, 2, 3
	jp PrintNum

Pokedex_DrawMainScreenBG:
; Draws the left sidebar and the bottom bar on the main screen.
	ld a, $32
	hlcoord 0, 0
	ld bc, SCREEN_AREA
	call ByteFill
	hlcoord 0, 0
	lb bc, 7, 7
	call Pokedex_PlaceBorder
	hlcoord 0, 8
	lb bc, 7, 6
	call Pokedex_PlaceBorder
	hlcoord 0, 8
	ldh a, [hCGB]
	and a
	ld a, POKEDEX_JOINED_LEFT_TILE
	jr z, .got_joined_left_tile
	ld a, POKEDEX_RESIDENT_JOINED_LEFT_TILE
.got_joined_left_tile
	ld [hli], a
	ldh a, [hCGB]
	and a
	ld a, POKEDEX_JOINED_MIDDLE_TILE
	jr z, .got_joined_middle_tile
	ld a, POKEDEX_RESIDENT_JOINED_MIDDLE_TILE
.got_joined_middle_tile
	ld bc, 6
	call ByteFill
	hlcoord 1, 10
	ld de, String_SEEN
	call Pokedex_PlaceString
	ld hl, wPokedexSeen
	ld bc, wEndPokedexSeen - wPokedexSeen
	call CountSetBits16
	ld a, c
	ld de, wPokedexDisplayNumber + 1
	ld [de], a
	dec de
	ld a, b
	ld [de], a
	hlcoord 4, 11
	lb bc, 2, 3
	call PrintNum
	hlcoord 1, 13
	ld de, String_OWN
	call Pokedex_PlaceString
	ld hl, wPokedexCaught
	ld bc, wEndPokedexCaught - wPokedexCaught
	call CountSetBits16
	ld a, c
	ld de, wPokedexDisplayNumber + 1
	ld [de], a
	dec de
	ld a, b
	ld [de], a
	hlcoord 4, 14
	lb bc, 2, 3
	call PrintNum
	ld a, $31
	hlcoord 0, 17
	ld bc, SCREEN_WIDTH
	call ByteFill
	hlcoord 1, 17
	ld de, String_SELECT_MODE
	call Pokedex_PlaceString
	hlcoord 8, 1
	ld b, 7
	ld a, $5a
	call Pokedex_FillColumn
	hlcoord 8, 0
	ld [hl], $59
	hlcoord 8, 2
	ld [hl], $6f
	hlcoord 8, 3
	ld [hl], $70

	hlcoord 7, 8
	ld a, POKEDEX_SCROLLBAR_TILE
	call .PlaceScrollbarRow
	ld b, 7
.scrollbar_middle
	ld a, POKEDEX_SCROLLBAR_TILE + 2
	call .PlaceScrollbarRow
	dec b
	jr nz, .scrollbar_middle
	ld a, POKEDEX_SCROLLBAR_TILE + 4
	call .PlaceScrollbarRow
	jp Pokedex_PlaceSelectedFrontpicTopLeftCorner

.PlaceScrollbarRow:
	ld [hli], a
	inc a
	ld [hl], a
	ld de, SCREEN_WIDTH - 1
	add hl, de
	ret

String_SEEN:
	db "Seen", -1
String_OWN:
	db "Own", -1
String_SELECT_MODE:
	db $3b, $48, $49, $4a, $4b, $4c, $4d, $4e ; SELECT > MODE
	; fallthrough
String_START_OPTION:
	db $3c, $3b, $41, $42, $43, $44, $45, $46, $47, $3c, -1 ; START > OPTION

Pokedex_DrawSearchScreenBG:
	call Pokedex_FillBackgroundColor2
.Header
	hlcoord 0, 0
	ld a, $31
	ld bc, 2 * SCREEN_WIDTH
	call ByteFill
	hlcoord 0, 2
	lb bc, 14, 18
	call Pokedex_PlaceBorder
	hlcoord 0, 1
	ld de, .Title
	call Pokedex_PlaceString
	hlcoord 7, 4
	ld de, .TypeLeftRightArrows
	call Pokedex_PlaceString
	hlcoord 7, 6
	ld de, .TypeLeftRightArrows
	call Pokedex_PlaceString
	hlcoord 2, 4
	ld de, .Types
	call PlaceString
	hlcoord 3, 13
	ld de, .Menu
	call PlaceString
	ret

.Title:
	db $3b, " Search ", $3c, -1

.TypeLeftRightArrows:
	db $3d, "        ", $3e, -1

.Types:
	db   "Type1"
	next "Type2"
	db   "@"

.Menu:
	db   "Begin Search!!"
	next "Cancel"
	db   "@"

Pokedex_DrawSearchResultsScreenBG:
	call Pokedex_FillBackgroundColor2
	hlcoord 0, 0
	lb bc, 7, 7
	call Pokedex_PlaceBorder
	hlcoord 0, 11
	lb bc, 5, 18
	call Pokedex_PlaceBorder
	hlcoord 1, 12
	ld de, .BottomWindowText
	call PlaceString
	ld de, wDexSearchResultCount
	hlcoord 1, 16
	call Pokedex_PrintLittleEndian
	hlcoord 8, 0
	ld [hl], $59
	hlcoord 8, 1
	ld b, 7
	ld a, $5a
	call Pokedex_FillColumn
	hlcoord 8, 8
	ld [hl], $53
	hlcoord 8, 9
	ld [hl], $69
	hlcoord 8, 10
	ld [hl], $6a
	call Pokedex_PlaceFrontpicTopLeftCorner
	ret

.BottomWindowText:
	db   "Search Results"
	next "  Type"
	next "    Found!"
	db   "@"
Pokedex_DrawUnownModeBG:
	hlcoord 0, 0
	ld bc, SCREEN_AREA
	ldh a, [hCGB]
	and a
	ld a, $32
	jr z, .fill_background
	ld a, $31 ; CGB outer backdrop is red; keep panel interiors dark gray.
.fill_background
	call ByteFill
	hlcoord 2, 1
	lb bc, 10, 13
	call Pokedex_PlaceBorder
	hlcoord 2, 14
	lb bc, 1, 13
	call Pokedex_PlaceBorder
	hlcoord 2, 15
	ld [hl], $3d
	hlcoord 16, 15
	ld [hl], $3e
	hlcoord 6, 5
	call Pokedex_PlaceFrontpicAtHL
	ldh a, [hCGB]
	and a
	jr z, .letters
	; Every resident-font overlay cell needs the bank-1 dark-gray blank.
	ld de, UnownModeLetterAndCursorCoords
	ld b, NUM_UNOWN * 2
.blank_overlay
	ld a, [de]
	inc de
	ld l, a
	ld a, [de]
	inc de
	ld h, a
	ld [hl], $32
	dec b
	jr nz, .blank_overlay
.letters
	ld de, 0
	ld b, 0
	ld c, NUM_UNOWN
.loop
	ld hl, wUnownDex
	add hl, de
	ld a, [hl]
	and a
	jr z, .done
	push af
	ld hl, UnownModeLetterAndCursorCoords
rept 4
	add hl, de
endr
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop af
	push bc
	ld c, a
	ldh a, [hCGB]
	and a
	ld a, c
	jr z, .dmg_letter
	add POKEDEX_RESIDENT_UNOWN_FONT_TILE - 1
	jr .place_letter
.dmg_letter
	add FIRST_UNOWN_CHAR - 1
.place_letter
	ld [hl], a
	pop bc
	inc de
	inc b
	dec c
	jr nz, .loop
.done
	ld a, b
	ld [wDexUnownCount], a
	ret

UnownModeLetterAndCursorCoords:
; entries correspond to Unown forms
;           letter, cursor
	dwcoord   4,11,   3,11 ; A
	dwcoord   4,10,   3,10 ; B
	dwcoord   4, 9,   3, 9 ; C
	dwcoord   4, 8,   3, 8 ; D
	dwcoord   4, 7,   3, 7 ; E
	dwcoord   4, 6,   3, 6 ; F
	dwcoord   4, 5,   3, 5 ; G
	dwcoord   4, 4,   3, 4 ; H
	dwcoord   4, 3,   3, 2 ; I
	dwcoord   5, 3,   5, 2 ; J
	dwcoord   6, 3,   6, 2 ; K
	dwcoord   7, 3,   7, 2 ; L
	dwcoord   8, 3,   8, 2 ; M
	dwcoord   9, 3,   9, 2 ; N
	dwcoord  10, 3,  10, 2 ; O
	dwcoord  11, 3,  11, 2 ; P
	dwcoord  12, 3,  12, 2 ; Q
	dwcoord  13, 3,  13, 2 ; R
	dwcoord  14, 3,  15, 2 ; S
	dwcoord  14, 4,  15, 4 ; T
	dwcoord  14, 5,  15, 5 ; U
	dwcoord  14, 6,  15, 6 ; V
	dwcoord  14, 7,  15, 7 ; W
	dwcoord  14, 8,  15, 8 ; X
	dwcoord  14, 9,  15, 9 ; Y
	dwcoord  14,10,  15,10 ; Z

Pokedex_FillBackgroundColor2:
	hlcoord 0, 0
	ld a, $32
	ld bc, SCREEN_AREA
	call ByteFill
	ret

Pokedex_PlaceFrontpicTopLeftCorner:
	hlcoord 1, 1
Pokedex_PlaceFrontpicAtHL:
	xor a
Pokedex_PlaceFrontpicAtHLWithTile:
	ld b, $7
.row
	ld c, $7
	push af
	push hl
.col
	ld [hli], a
	add $7
	dec c
	jr nz, .col
	pop hl
	ld de, SCREEN_WIDTH
	add hl, de
	pop af
	inc a
	dec b
	jr nz, .row
	ret

Pokedex_PlaceSelectedFrontpicTopLeftCorner:
	jr Pokedex_PlaceFrontpicTopLeftCorner

Pokedex_PlaceString:
.loop
	ld a, [de]
	cp -1
	ret z
	inc de
	ld [hli], a
	jr .loop

Pokedex_PlaceBorder:
	push hl
	ld a, $33
	ld [hli], a
	ld d, $34
	call .FillRow
	ld a, $35
	ld [hl], a
	pop hl
	ld de, SCREEN_WIDTH
	add hl, de
.loop
	push hl
	ld a, $36
	ld [hli], a
	ld d, $7f
	call .FillRow
	ld a, $37
	ld [hl], a
	pop hl
	ld de, SCREEN_WIDTH
	add hl, de
	dec b
	jr nz, .loop
	ld a, $38
	ld [hli], a
	ld d, $39
	call .FillRow
	ld a, $3a
	ld [hl], a
	ret

.FillRow:
	ld e, c
.row_loop
	ld a, e
	and a
	ret z
	ld a, d
	ld [hli], a
	dec e
	jr .row_loop

Pokedex_LoadGridPage:
	ld hl, wPokedexGridOccupied
	ld bc, 3 * POKEDEX_GRID_SIZE
	xor a
	call ByteFill

	xor a
.cache_loop
	push af
	call Pokedex_CacheGridPosition
	pop af
	inc a
	cp POKEDEX_GRID_SIZE
	jr c, .cache_loop

	ret

Pokedex_CacheGridPosition:
; Cache one visible entry. Input: a = grid position.
	ld [wDexTempCounter], a
	ld e, a
	ld d, 0
	ld hl, wPokedexGridOccupied
	add hl, de
	xor a
	ld [hl], a
	ld hl, wPokedexGridFlags
	add hl, de
	ld [hl], a
	ld hl, wPokedexGridIconPalettes
	add hl, de
	ld [hl], a
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a
	add hl, de
	push hl
	ld a, [wDexListingEnd]
	ld e, a
	ld a, [wDexListingEnd + 1]
	ld d, a
	pop hl
	ld a, l
	sub e
	ld a, h
	sbc d
	ret nc

	add hl, hl
	ld de, wPokedexOrder
	add hl, de
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	ld a, [hli]
	ld c, a
	ld b, [hl]
	pop af
	ldh [rSVBK], a
	ld a, b
	and c
	inc a
	ret z

	ld h, b
	ld l, c
	push hl
	call GetPokemonIDFromIndex
	ld [wTempSpecies], a
	ld a, [wDexTempCounter]
	ld e, a
	ld d, 0
	ld hl, wPokedexGridOccupied
	add hl, de
	ld [hl], TRUE
	ld hl, wPokedexGridFlags
	add hl, de
	ld [hl], 0
	pop de

	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexSeen)
	ldh [rSVBK], a
	push de
	call CheckSeenMonIndex
	pop de
	jr z, .not_seen
	ld a, [wDexTempCounter]
	ld c, a
	ld b, 0
	ld hl, wPokedexGridFlags
	add hl, bc
	set POKEDEX_GRID_SEEN_F, [hl]
.not_seen
	push de
	call CheckCaughtMonIndex
	pop de
	jr z, .not_caught
	ld a, [wDexTempCounter]
	ld c, a
	ld b, 0
	ld hl, wPokedexGridFlags
	add hl, bc
	set POKEDEX_GRID_CAUGHT_F, [hl]
.not_caught
	pop af
	ldh [rSVBK], a
	ld a, [wTempSpecies]
	ld c, a
	farcall Pokedex_CacheGridIconPalette
	ret

Pokedex_PrintSelectedName:
	hlcoord 0, 1
	ld bc, 11
	ld a, ' '
	call ByteFill
	call Pokedex_GetSelectedMon
	call Pokedex_CheckSeen
	jr z, .unseen
	ld d, h
	ld e, l
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
	ld de, wPokedexNameBuffer
	jr .place

.unseen
	ld de, .UnseenName
.place
	hlcoord 0, 1
	jp PlaceString

.UnseenName:
	db "-----@"

Pokedex_PrintNumberIfOldMode:
	ld a, [wCurDexMode]
	cp DEXMODE_OLD
	ret nz
	push hl
	push de
	ld bc, -SCREEN_WIDTH
	add hl, bc
	ld a, e
	ld [wPokedexDisplayNumber + 1], a
	ld a, d
	ld de, wPokedexDisplayNumber
	ld [de], a
	lb bc, PRINTNUM_LEADINGZEROS | 2, 3
	call PrintNum
	pop de
	pop hl
	ret

Pokedex_PlaceDefaultStringIfNotSeen:
	push hl
	push de
	call CheckSeenMonIndex
	pop de
	pop hl
	ret nz
	inc hl
	ld de, .NameNotSeen
	call PlaceString
	scf
	ret

.NameNotSeen:
	db "-----@"

Pokedex_DrawFootprint:
	hlcoord 18, 1
	ld a, $62
	jr Pokedex_DrawFootprintWithTile

Pokedex_DrawResidentFootprint:
	ldh a, [hCGB]
	and a
	jr z, Pokedex_DrawFootprint
	ld a, POKEDEX_RESIDENT_FOOTPRINT_TILE
	hlcoord 18, 1
Pokedex_DrawFootprintWithTile:
	ld [hli], a
	inc a
	ld [hl], a
	inc a
	hlcoord 18, 2
	ld [hli], a
	inc a
	ld [hl], a
	ret

Pokedex_GetSelectedMon:
	ld hl, wDexListingEnd
	ld a, [hli]
	or [hl]
	jr nz, .nonempty
	ld hl, CHIKORITA
	jp Pokedex_ResolveSpeciesIndex
.nonempty
; Gets the species of the currently selected Pokémon. This corresponds to the
; position owned by the active Pokédex section.
	ld a, [wJumptableIndex]
	cp DEXSTATE_SELECTED_MON_ENTER
	jr c, .listing_selection
	cp DEXSTATE_SELECTED_MON_RESERVED + 1
	jr nc, .listing_selection
	ld hl, wPokedexSelectedIndex
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jr Pokedex_GetMonAtOrderIndex

.listing_selection
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [wDexListingCursor]
	ld e, a
	ld d, 0
	add hl, de
	; fallthrough

Pokedex_GetMonAtOrderIndex:
; hl = absolute entry index in wPokedexOrder.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	ld de, wPokedexOrder
	add hl, hl
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop af
	ldh [rSVBK], a
Pokedex_ResolveSpeciesIndex:
	push hl
	call GetPokemonIDFromIndex
	ld l, LOCKED_MON_ID_DEX_SELECTED
	call LockPokemonID
	pop hl
	ld [wTempSpecies], a
	ret

Pokedex_GetSelectionRenderKey:
; Known selections use their species ID. All unseen selections share one key
; because their name, frontpic, and palette are identical.
	call Pokedex_GetSelectedMon
	call Pokedex_CheckSeen
	ld a, POKEDEX_RENDER_KEY_UNSEEN
	ret z
	ld a, [wTempSpecies]
	ret

Pokedex_RecordRenderedSelectionKey:
	ld a, [wCurPartySpecies]
	ld [wPokedexRenderedSelectionKey], a
	ret

Pokedex_CheckSeen:
	push de
	push hl
	ld a, [wTempSpecies]
	call CheckSeenMon
	pop hl
	pop de
	ret

Pokedex_UpdateSearchMonType:
	ld a, [wDexArrowCursorPosIndex]
	cp 2
	jr nc, .no_change
	ld hl, hJoyLast
	ld a, [hl]
	and PAD_LEFT
	jr nz, Pokedex_PrevSearchMonType
	ld a, [hl]
	and PAD_RIGHT
	jr nz, Pokedex_NextSearchMonType
.no_change
	and a
	ret

Pokedex_PrevSearchMonType:
	ld a, [wDexArrowCursorPosIndex]
	and a
	jr nz, .type2

	ld hl, wDexSearchMonType1
	ld a, [hl]
	cp 1
	jr z, .wrap_around
	dec [hl]
	jr .done

.type2
	ld hl, wDexSearchMonType2
	ld a, [hl]
	and a
	jr z, .wrap_around
	dec [hl]
	jr .done

.wrap_around
	ld [hl], NUM_TYPES

.done
	scf
	ret

Pokedex_NextSearchMonType:
	ld a, [wDexArrowCursorPosIndex]
	and a
	jr nz, .type2

	ld hl, wDexSearchMonType1
	ld a, [hl]
	cp NUM_TYPES
	jr nc, .type1_wrap_around
	inc [hl]
	jr .done
.type1_wrap_around
	ld [hl], 1
	jr .done

.type2
	ld hl, wDexSearchMonType2
	ld a, [hl]
	cp NUM_TYPES
	jr nc, .type2_wrap_around
	inc [hl]
	jr .done
.type2_wrap_around
	ld [hl], 0

.done
	scf
	ret

Pokedex_PlaceSearchScreenTypeStrings:
	farcall PokedexSearch_DrawFields
	farcall PokedexSearch_UpdateIcons
	ld a, 1
	ldh [hBGMapMode], a
	ret

PokedexSearch_DrawFieldText:
	ldh a, [hCGB]
	and a
	jr nz, .second
	ld a, [wDexSearchMonType1]
	hlcoord 8, 4
	call Pokedex_PlaceTypeString
.second
	ldh a, [hCGB]
	and a
	jr z, .text
	ld a, [wDexSearchMonType2]
	and a
	ret nz
.text
	ld a, [wDexSearchMonType2]
	hlcoord 8, 6
	jp Pokedex_PlaceTypeString

Pokedex_PlaceTypeString:
	push hl
	ld e, a
	ld d, 0
	ld hl, PokedexTypeSearchStrings
rept POKEDEX_TYPE_STRING_LENGTH
	add hl, de
endr
	ld e, l
	ld d, h
	pop hl
	call PlaceString
	ret

INCLUDE "data/types/search_strings.asm"

Pokedex_SearchForMons:
	farcall PokedexSearch_Filter
	ret

INCLUDE "data/types/search_types.asm"

Pokedex_DisplayTypeNotFoundMessage:
	xor a
	ldh [hBGMapMode], a
	hlcoord 0, 12
	lb bc, 4, 18
	call Pokedex_PlaceBorder
	ld de, .TypeNotFound
	hlcoord 1, 14
	call PlaceString
	ld a, $1
	ldh [hBGMapMode], a
	ld c, $80
	call DelayFrames
	ret

.TypeNotFound:
	db   "The specified type"
	next "was not found.@"

Pokedex_PutScrollbarOAM:
	push de
	ld hl, wDexListingEnd
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [wDexListingHeight]
	cpl
	ld c, a
	ld b, $FF
	; subtract wDexListingHeight + 1 so it will also overflow on wDexListingEnd = wDexListingHeight
	add hl, bc
	inc b ;b = 0
	jr nc, .done
	inc hl ;compensate for the +1
	push hl
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a
	; multiply by 121 (scrollbar size) - first by 15...
	; (assume that the dex has less than $1000 entries - it won't fit in any RAM otherwise)
	ld b, h
	ld c, l
	rept 4
		add hl, hl
	endr
	ld a, l
	sub c
	ld l, a
	ld a, h
	sbc b
	ld h, a
	; ...then by 8 (15 * 8 = 120), storing overflows in a...
	xor a
	rept 3
		add hl, hl
		adc a
	endr
	; ...and add the original value, for a full result of ahl = wDexListingScrollOffset * 121
	add hl, bc
	adc 0
	; finally, double the value (for rounding after dividing) and transfer it to chl
	add hl, hl
	adc a
	ld c, a
	; load the scroll height (pushed before) back into de, and multiply by -16...
	pop de
	push de
	swap d
	swap e
	ld a, e
	and $f
	or d
	cpl
	ld d, a
	ld a, e
	and $f0
	cpl
	ld e, a
	inc de
	; ...and use it to calculate the upper nibble of the quotient by subtraction
	inc c
	ld b, 0
.upper_loop
	inc b
	add hl, de
	jr c, .upper_loop
	dec c
	jr nz, .upper_loop
	res 4, b ;ensure overflow doesn't leave garbage behind
	swap b
	; now there's a negative value in hl and an overly large result in b - adjust until the right value is found
	pop de
.lower_loop
	dec b
	add hl, de
	jr nc, .lower_loop
	; the result is in b - which is twice the true quotient, so increment and halve to round to nearest
	inc b
	srl b
.done
	ld a, 20 ; min y
	add b
	pop hl
	ld [hli], a
	ld a, 161 ; x
	ld [hli], a
	ld a, $0f ; tile id
	ld [hli], a
	ld [hl], 0 ; attributes
	ret

Pokedex_InitArrowCursor:
	xor a
	ld [wDexArrowCursorPosIndex], a
	ld [wDexArrowCursorDelayCounter], a
	jp Pokedex_ResetArrowCursorBlink

Pokedex_MoveArrowCursor:
; bc = [de] - 1
	ld a, [de]
	ld b, a
	inc de
	ld a, [de]
	dec a
	ld c, a
	inc de
	call Pokedex_BlinkArrowCursor

	ld hl, hJoyPressed
	ld a, [hl]
	and PAD_LEFT | PAD_UP
	and b
	jr nz, .move_left_or_up
	ld a, [hl]
	and PAD_RIGHT | PAD_DOWN
	and b
	jr nz, .move_right_or_down
	ld a, [hl]
	and PAD_SELECT
	and b
	jr nz, .select
	call Pokedex_ArrowCursorDelay
	jr c, .no_action
	ld hl, hJoyLast
	ld a, [hl]
	and PAD_LEFT | PAD_UP
	and b
	jr nz, .move_left_or_up
	ld a, [hl]
	and PAD_RIGHT | PAD_DOWN
	and b
	jr nz, .move_right_or_down
	jr .no_action

.move_left_or_up
	ld a, [wDexArrowCursorPosIndex]
	and a
	jr z, .no_action
	call Pokedex_GetArrowCursorPos
	ld [hl], ' '
	ld hl, wDexArrowCursorPosIndex
	dec [hl]
	jr .update_cursor_pos

.move_right_or_down
	ld a, [wDexArrowCursorPosIndex]
	cp c
	jr nc, .no_action
	call Pokedex_GetArrowCursorPos
	ld [hl], ' '
	ld hl, wDexArrowCursorPosIndex
	inc [hl]

.update_cursor_pos
	call Pokedex_GetArrowCursorPos
	ld [hl], '▶'
	ld a, 12
	ld [wDexArrowCursorDelayCounter], a
	call Pokedex_ResetArrowCursorBlink
	scf
	ret

.no_action
	and a
	ret

.select
	call Pokedex_GetArrowCursorPos
	ld [hl], ' '
	ld a, [wDexArrowCursorPosIndex]
	cp c
	jr c, .update
	ld a, -1
.update
	inc a
	ld [wDexArrowCursorPosIndex], a
	jr .update_cursor_pos

Pokedex_GetArrowCursorPos:
	ld a, [wDexArrowCursorPosIndex]
	add a
	ld l, a
	ld h, 0
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret

Pokedex_BlinkArrowCursor:
	call Pokedex_AdvanceArrowCursorBlink
	ld a, ' '
	jr nz, .tile
	ld a, '▶'
.tile
	push af
	call Pokedex_GetArrowCursorPos
	pop af
	ld [hl], a
	ret

Pokedex_ResetArrowCursorBlink::
	xor a
	ld [wDexArrowCursorBlinkCounter], a
	ret

; Shared by BG, shifted BG, and OBJ arrows. Z means visible for this update.
Pokedex_AdvanceArrowCursorBlink::
	ld hl, wDexArrowCursorBlinkCounter
	ld a, [hl]
	inc [hl]
	and $8
	ret

Pokedex_ArrowCursorDelay:
; Updates the delay counter set when moving the arrow cursor.
; Returns whether the delay is active in carry.
	ld hl, wDexArrowCursorDelayCounter
	ld a, [hl]
	and a
	ret z

	dec [hl]
	scf
	ret

Pokedex_FillBox:
	jp FillBoxWithByte

Pokedex_BlackOutBG:
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rWBK], a
	ld hl, wBGPals1
	ld bc, 8 palettes
	xor a
	call ByteFill
	pop af
	ldh [rWBK], a
	ret

Pokedex_GetDexSGBLayout:
	ld a, SCGB_POKEDEX
	; fallthrough
Pokedex_GetSGBLayout:
	ld b, a
	call GetSGBLayout
	ld a, [wJumptableIndex]
	cp DEXSTATE_MAIN_SCR
	ret z
	cp DEXSTATE_UPDATE_MAIN_SCR
	ret z

Pokedex_ApplyUsualPals:
; This applies the palettes used for most Pokédex screens.
	ld a, $e4
	call DmgToCgbBGPals
	ld a, $e0
	jp DmgToCgbObjPal0

Pokedex_LoadPointer:
	ld e, a
	ld d, 0
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret

Pokedex_LoadSelectedMonTiles:
; Loads the tiles of the currently selected Pokémon.
	call Pokedex_GetSelectedMon
	call Pokedex_CheckSeen
	jr z, .QuestionMark
	ld a, [wFirstUnownSeen]
	ld [wUnownLetter], a
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	call GetBaseData
	ld de, vTiles2
	predef GetMonFrontpic
	ldh a, [hCGB]
	and a
	ret z
	jp Pokedex_LoadCurrentFootprint

.QuestionMark:
	ld a, -1
	ld [wCurPartySpecies], a
	ld a, BANK(sScratch)
	call OpenSRAM
	farcall LoadQuestionMarkPic
	ld hl, vTiles2
	ld de, sScratch
	ld c, 7 * 7
	ldh a, [hROMBank]
	ld b, a
	call Get2bpp
	jp CloseSRAM

Pokedex_PrepareSelectedMonTiles:
; Build one complete 7x7 selection image in Dex-only WRAM0. The currently
; displayed vTiles2 image remains untouched until Pokedex_CommitStagedSelection.
	call Pokedex_GetSelectedMon
	call Pokedex_CheckSeen
	jr z, .question_mark
	ld a, [wFirstUnownSeen]
	ld [wUnownLetter], a
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	ld [wCurSpecies], a
	ldh a, [rWBK]
	push af
	ld a, BANK(sEnemyFrontPicTileCount)
	call OpenSRAM
	farcall Pokedex_PrepareFrontpicBase
	pop af
	ldh [rWBK], a
	call CloseSRAM
	ld a, [wCurPartySpecies]
	ld [wTempSpecies], a
	jp Pokedex_PrepareCurrentFootprint

.question_mark
	ld a, -1
	ld [wCurPartySpecies], a
	ld a, BANK(sScratch)
	call OpenSRAM
	farcall LoadQuestionMarkPic
	ld hl, sScratch
	ld de, wPokedexWRAM0Scratch
	ld bc, 7 * 7 tiles
	call CopyBytes
	jp CloseSRAM

Pokedex_LoadCurrentFootprint:
	call Pokedex_GetSelectedMon
	ldh a, [hCGB]
	and a
	jr z, Pokedex_LoadAnyFootprint
	ld a, [wPokedexResidentFootprintSpecies]
	ld hl, wTempSpecies
	cp [hl]
	ret z
	call Pokedex_PrepareCurrentFootprint
	call Pokedex_TransferPreparedFootprint
	ld a, [wTempSpecies]
	ld [wPokedexResidentFootprintSpecies], a
	ret

Pokedex_LoadAnyFootprint:
	call Pokedex_GetFootprintPointer
	ld hl, vTiles2 tile $62
	lb bc, BANK(Footprints), 4
	jp Get1bpp

Pokedex_PrepareCurrentFootprint:
	call Pokedex_GetFootprintPointer
	ld h, d
	ld l, e
	ld de, wPokedexWRAM0Scratch + 7 * 7 tiles
	ld bc, 4 * TILE_1BPP_SIZE
	ld a, BANK(Footprints)
	jp FarCopyBytesDouble

Pokedex_GetFootprintPointer:
	ld a, [wTempSpecies]
	call GetPokemonIndexFromID
	dec hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, Footprints
	add hl, de
	ld e, l
	ld d, h
	ret

Pokedex_TransferPreparedFootprint:
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch + 7 * 7 tiles
	ld de, vTiles4 tile $31
	ld c, 4
	call Pokedex_HDMATransferSelectionGFX
	pop af
	ldh [rVBK], a
	ret

Pokedex_LoadGFX:
	ld a, -1
	ld [wPokedexResidentFootprintSpecies], a
	call DisableLCD
	ld hl, vTiles2
	ld bc, $31 tiles
	xor a
	call ByteFill
	call Pokedex_LoadInvertedFont
	call LoadFontsExtra
	ld hl, vTiles2 tile $60
	ld bc, $20 tiles
	call Pokedex_InvertTiles
	call Pokedex_MakeSpaceTileDarkGray

.LoadPokedexLZ:
	ld hl, PokedexLZ
	ld de, vTiles2 tile $31
	call Decompress

.LoadPokedexSlowpokeLZ:
	ld hl, PokedexSlowpokeLZ
	ld de, vTiles0
	call Decompress
	call Pokedex_LoadListStaticGFX
	farcall Pokedex_LoadPermanentCGBGFX
	ld a, 6
	call SkipMusic
	ret

Pokedex_LoadListStaticGFX:
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld de, PokedexScrollbarGFX
	ld hl, vTiles1 tile (POKEDEX_SCROLLBAR_TILE - $80)
	lb bc, BANK(PokedexScrollbarGFX), 6
	call Get2bpp
	ld de, PokedexUnseenGFX
	ld hl, vTiles1 tile (POKEDEX_UNSEEN_TILE - $80)
	lb bc, BANK(PokedexUnseenGFX), 4
	call Get2bpp
	ld de, PokedexListCursorGFX
	ld hl, vTiles0 tile POKEDEX_LIST_CURSOR_TILE
	lb bc, BANK(PokedexListCursorGFX), 1
	call Get2bpp
	ld de, PokedexCaughtBallGFX
	ld hl, vTiles0 tile POKEDEX_CAUGHT_BALL_TILE
	lb bc, BANK(PokedexCaughtBallGFX), 1
	call Get2bpp
	pop af
	ldh [rVBK], a
	ret

Pokedex_LoadListJoinedBorderGFX:
	ldh a, [hCGB]
	and a
	ret nz
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld de, PokedexListJoinedLeftGFX
	ld hl, vTiles2 tile POKEDEX_JOINED_LEFT_TILE
	lb bc, BANK(PokedexListJoinedLeftGFX), 1
	call Get2bpp
	ld de, PokedexListJoinedMiddleGFX
	ld hl, vTiles2 tile POKEDEX_JOINED_MIDDLE_TILE
	lb bc, BANK(PokedexListJoinedMiddleGFX), 1
	call Get2bpp
	pop af
	ldh [rVBK], a
	ret

Pokedex_LoadInvertedFont:
	call LoadStandardFont
	ld hl, vTiles1
	ld bc, $80 * TILE_1BPP_SIZE
.row
	xor a
	ld [hli], a
	ld a, [hl]
	xor $ff
	ld [hli], a
	dec bc
	ld a, b
	or c
	jr nz, .row
	ret

Pokedex_MakeSpaceTileDarkGray:
	ld hl, vTiles2 tile ' '
Pokedex_MakeTileDarkGray:
	ld b, TILE_WIDTH
.row
	xor a
	ld [hli], a
	dec a
	ld [hli], a
	dec b
	jr nz, .row
	ret

Pokedex_MakeTileDarkGrayAtDE:
	ld h, d
	ld l, e
	jr Pokedex_MakeTileDarkGray

Pokedex_InvertTiles:
.loop
	ld a, [hl]
	xor $ff
	ld [hli], a
	dec bc
	ld a, b
	or c
	jr nz, .loop
	ret

PokedexLZ:
INCBIN "gfx/pokedex/pokedex_core.2bpp.lz"

PokedexSlowpokeLZ:
INCBIN "gfx/pokedex/slowpoke_dex.2bpp.lz"

Pokedex_LoadUnownFont:
	ld a, BANK(sScratch)
	call OpenSRAM
	ld hl, UnownFont
	; sScratch + $188 was the address of sDecompressBuffer in pokegold
	ld de, sScratch + $188
	ld bc, 39 tiles
	ld a, BANK(UnownFont)
	call FarCopyBytes
	ld hl, sScratch + $188
	ld bc, (NUM_UNOWN + 1) tiles
	call Pokedex_InvertTiles
	ldh a, [rVBK]
	push af
	ldh a, [hCGB]
	and a
	jr z, .dmg
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	ld hl, vTiles4 tile $35
	jr .load
.dmg
	xor a
	ldh [rVBK], a
	ld hl, vTiles2 tile FIRST_UNOWN_CHAR
.load
	ld de, sScratch + $188
	lb bc, BANK(Pokedex_LoadUnownFont), NUM_UNOWN + 1
	call Get2bpp
	pop af
	ldh [rVBK], a
	call CloseSRAM
	ret

Pokedex_LoadUnownFrontpicTiles:
	ld a, [wUnownLetter]
	push af
	ld a, [wDexCurUnownIndex]
	ld e, a
	ld d, 0
	ld hl, wUnownDex
	add hl, de
	ld a, [hl]
	ld [wUnownLetter], a
	ld hl, UNOWN
	call GetPokemonIDFromIndex
	ld [wCurPartySpecies], a
	ld l, LOCKED_MON_ID_DEX_SELECTED
	call LockPokemonID
	ldh a, [hCGB]
	and a
	jr z, .dmg
	farcall PokedexUnown_PreparePicture
	pop af
	ld [wUnownLetter], a
	ret
.dmg
	call GetBaseData
	ld de, vTiles2 tile $00
	predef GetMonFrontpic
	pop af
	ld [wUnownLetter], a
	ret

_NewPokedexEntry:
	xor a
	ldh [hBGMapMode], a
	ld [wPokedexDescriptionPage], a
	call Pokedex_ResetBGMapMode
	call Pokedex_LoadGFX
	farcall Pokedex_CopyDescriptionRightEdge
	call Pokedex_LoadAnyFootprint
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	farcall Pokedex_DrawDescriptionScreenBG
	call Pokedex_DrawFootprint
	hlcoord 0, 17
	ld bc, SCREEN_WIDTH
	ld a, $31
	call ByteFill
	ld [vBGMap0 + 17 * TILEMAP_WIDTH + SCREEN_WIDTH], a
	farcall Pokedex_DisplayDescriptionEntry
	call EnableLCD
	call WaitBGMap
	call GetBaseData
	farcall NewDexEntry_LoadAnimatedFrontpic
	hlcoord 1, 1
	ld d, $0
	ld e, ANIM_MON_MENU
	predef LoadMonAnimation
	ld a, 1
	ld [wFrameCounter], a
	farcall NewDexEntry_VisualLayout
	call DelayFrame
	ret

Pokedex_SetBGMapMode3:
	ld a, $3
	ldh [hBGMapMode], a
	ld c, 4
	call DelayFrames
	ret

Pokedex_ResetBGMapMode:
	xor a
	ldh [hBGMapMode], a
	ret

PokedexResults_PrintNames:
; Prints the list of Pokémon on the main Pokédex screen.

	ld c, 11
; Clear (2 * [wDexListingHeight] + 1) by 11 box starting at 0,1
	hlcoord 0, 1
	ld a, [wDexListingHeight]
	add a
	inc a
	ld b, a
	ld a, ' '
	call Pokedex_FillBox

; Load de with a pointer to the first mon on the list
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a
	add hl, hl
	ld de, wPokedexOrder
	add hl, de
	ld e, l
	ld d, h
	hlcoord 0, 2
	ldh a, [rSVBK]
	push af
	ld a, [wDexListingHeight]
.loop
	push af
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	ld a, [de]
	ld c, a
	inc de
	ld a, [de]
	inc de
	push de
	ld d, a
	ld e, c
	or e
	push hl
	call nz, .PrintEntry
	pop hl
	ld de, 2 * SCREEN_WIDTH
	add hl, de
	pop de
	pop af
	dec a
	jr nz, .loop
	pop af
	ldh [rSVBK], a
	ret

.PrintEntry:
	ld a, d
	and e
	inc a
	ret z
	ld a, BANK(wPokedexSeen)
	ldh [rSVBK], a
	call Pokedex_PrintNumberIfOldMode
	call Pokedex_PlaceDefaultStringIfNotSeen
	ret c
	inc hl
	push hl
	; hl = de * 10 (length of a Pokémon name)
	ld h, d
	ld l, e
	add hl, hl
	add hl, hl
	add hl, de
	add hl, hl
	ld de, PokemonNames - (MON_NAME_LENGTH - 1) ;correct for the one-based indexing
	add hl, de
	ld a, BANK(PokemonNames)
	ld bc, MON_NAME_LENGTH - 1
	ld de, wPokedexNameBuffer
	push de
	call FarCopyBytes
	ld a, '@'
	ld [wPokedexNameBuffer + MON_NAME_LENGTH - 1], a
	pop de
	pop hl
	jp PlaceString


PokedexResults_DrawBG:
    call Pokedex_DrawSearchResultsScreenBG
    hlcoord 0, 9
    lb bc, 2, 8
    ld a, $31
    call Pokedex_FillBox
    farcall CGB_PokedexResultsAttributes
    ret
