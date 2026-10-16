; Fixed-species Selected-style registration. No Listing order or bookmarks.
DEF NEW_DEX_REG_FIELDS EQU 31
DEF NEW_DEX_REG_FIELDS_AT EQUS "wTempTilemap + $20"
DEF NEW_DEX_REG_PREV EQUS "NEW_DEX_REG_FIELDS_AT + NEW_DEX_REG_FIELDS"
DEF NEW_DEX_REG_LOCK EQUS "NEW_DEX_REG_PREV + 2"
DEF NEW_DEX_REG_CONTEXT_END EQUS "NEW_DEX_REG_LOCK + 2"
ASSERT NEW_DEX_REG_CONTEXT_END - wTempTilemap == 67
ASSERT NEW_DEX_REG_CONTEXT_END <= wPokeAnimStruct
ASSERT BANK(wTempTilemap) == 2

NewPokedexEntry:
	ldh a, [rSVBK]
	push af
	ld a, 1
	ldh [rSVBK], a
	ld a, [wBattleMode]
	and a
	jr z, .producer_ready
	farcall BattleFrontpicProducer_Finish
.producer_ready
	farcall WaitDMATransfer
	call NewDexRegistration_SaveContext
	call NewDexRegistration_Initialize
	call NewDexRegistration_Prepare
NewDexRegistration_Revealed::
	farcall PokedexSelectedMon_Reveal
	farcall Pokedex_BeginPreparedDescriptionAnimation
NewDexRegistration_Loop::
	farcall Pokedex_BeginOwnerLoop
NewDexRegistration_Input::
	farcall PokedexSelectedMon_ReadFooterCursor
	farcall PokedexSelectedMon_CommitFooterCursor
	ldh a, [hJoyPressed]
	and PAD_B
	jp nz, NewDexRegistration_Leave
	ldh a, [hJoyPressed]
	and PAD_A
	jr z, .service
	ld a, [wDexArrowCursorPosIndex]
	cp 3
	jp z, NewDexRegistration_Leave
	farcall PokedexSelectedMon_ActivateFooterView
.service
	farcall Pokedex_PrepareDescriptionAnimation
	farcall Pokedex_ServiceAnimationProducer
	farcall Pokedex_CommitDescriptionAnimation
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_MOVES
	jr nz, .not_moves
	farcall PokedexMoves_Service
	jr .paced
.not_moves
	cp DEXSELECT_VIEW_INFO
	jr nz, .description
	farcall PokedexInfo_Service
	jr .paced
.description
	farcall PokedexSelectedMon_ServiceDescriptionText
.paced
	farcall Pokedex_EndOwnerLoop
	jp NewDexRegistration_Loop

NewDexRegistration_Initialize:
	xor a
	ldh [hMapAnims], a
	ldh [hLCDCPointer], a
	ldh [hVBlank], a
	ldh [hBGMapMode], a
	ldh [hSCY], a
	ldh [hMapObjectIndex], a
	ld [wPokedexSelectedView], a
	ld [wPokedexDescriptionPage], a
	ld [wPokedexStatus], a
	ld [wPokedexOwnerTransition], a
	ld [wPokedexSelectedBGPaletteDirty], a
	ld [wPokedexSelectedOBJPaletteDirty], a
	ld [wStateFlags], a
	ld [POKEDEX_DESCRIPTION_ICON_BUFFER], a
	ld a, 1
	ldh [hInMenu], a
	ld a, 6
	ldh [hObjectStructIndex], a
	ld a, POKEDEX_SCX
	ldh [hSCX], a
	ld a, $a7
	ldh [hWX], a
	ld a, $90
	ldh [hWY], a
	ld hl, wOptions
	set NO_TEXT_SCROLL, [hl]
	ld a, DEXSTATE_SELECTED_MON_UPDATE
	ld [wJumptableIndex], a
	ld a, DEXSELECT_STATE_ENTERING
	ld [wPokedexSelectedState], a
	ld a, DEXSTATE_EXIT
	ld [wPokedexSelectedReturnState], a
	call LowVolume
	call ClearBGPalettes
	call ClearSprites
	ld a, TRUE
	ldh [hOAMUpdate], a
	farcall Pokedex_CancelAnimationPrefetch
	farcall PokedexInfo_Reset
	ld a, [wTempSpecies]
	ld [wPokedexSelectedSpecies], a
	ld [wCurPartySpecies], a
	ld [wCurSpecies], a
	push af
	call GetPokemonIndexFromID
	ld a, l
	ld [wPrevDexEntry], a
	ld a, h
	ld [wPrevDexEntry + 1], a
	pop af
	ld l, LOCKED_MON_ID_DEX_SELECTED
	call LockPokemonID
	ret

NewDexRegistration_Prepare:
	farcall Pokedex_LoadGFX
	farcall Pokedex_CopyDescriptionRightEdge
	farcall Pokedex_DrawDescriptionScreenBG
	hlcoord 16, 17
	ld de, .End
	call PlaceString
	farcall Pokedex_InitArrowCursor
	farcall Pokedex_DisplayDescriptionEntry
	ld a, BANK(sEnemyFrontPicTileCount)
	call OpenSRAM
	farcall Pokedex_PrepareFrontpicBase
	ld a, 1
	ldh [rSVBK], a
	call CloseSRAM
	farcall Pokedex_PrepareCurrentFootprint
	farcall Pokedex_CommitPreparedSelectedMonGFX
	farcall PokedexSelectedMon_DrawFootprint
	; Selected's type uploader needs HBlank; keep the palette hidden until reveal.
	call EnableLCD
	; Type staging shares the picture payload: finish it before priming.
	farcall Pokedex_LoadDescriptionTypeGFX
	farcall Pokedex_PrimeDescriptionAnimation
	farcall CGB_PokedexStageSelectedMonLayout
	farcall PokedexSelectedMon_StageUsualPals
	farcall PokedexInfo_StageTypePalettes
	farcall PokedexInfo_StageStaticPalettes
	farcall PokedexInfo_PrepareSpecies
	xor a
	ldh [hCGBPalUpdate], a
	farcall Pokedex_StageInitialAnimationFrame
	farcall Pokedex_PublishOrStageDescriptionBacking
	ld a, DEXSELECT_STATE_ACTIVE
	ld [wPokedexSelectedState], a
	ret
.End:
	db "End @"

NewDexRegistration_Leave::
	farcall PokedexSelectedMon_CancelDescriptionText
	farcall PokedexInfo_Cancel
	farcall PokedexSelectedMon_CancelCry
	farcall Pokedex_CancelAnimationPrefetch
	xor a
	ld [wPokedexOwnerTransition], a
	ld [wPokedexSelectedBGPaletteDirty], a
	ld [wPokedexSelectedOBJPaletteDirty], a
	ldh [hVBlank], a
	ldh [hBGMapMode], a
	ldh [hOAMUpdate], a
	call ClearSprites
	call RotateThreePalettesRight
	call NewDexRegistration_RestoreContext
	; The old caller owns the post-catch DV/font/palette continuation.
	call NewPokedexEntry_ReturnFromDexRegistration
	pop af
	ldh [rSVBK], a
NewDexRegistration_Returned::
	ret

NewPokedexEntry_ReturnFromDexRegistration:
	call ClearTilemap
	call LoadFontsExtra
	call LoadStandardFont
	farcall Pokedex_PlaceFrontpicTopLeftCorner
	call WaitBGMap2
	farcall GetEnemyMonDVs
	ld a, [hli]
	ld [wTempMonDVs], a
	ld a, [hl]
	ld [wTempMonDVs + 1], a
	ld b, SCGB_TRAINER_OR_MON_FRONTPIC_PALS
	call GetSGBLayout
	call SetDefaultBGPAndOBP
	ret

NewDexRegistration_SaveContext:
	ld a, 2
	ldh [rSVBK], a
	ld hl, wBattleMenuGFXFlags
	ld de, wTempTilemap
	ld bc, $20
	call CopyBytes
	ld hl, NewDexRegistration_Fields
	ld de, NEW_DEX_REG_FIELDS_AT
	ld b, NEW_DEX_REG_FIELDS
.field
	push bc
	ld a, [hli]
	ld c, a
	ld a, [hli]
	push hl
	ld h, a
	ld l, c
	ld a, 1
	ldh [rSVBK], a
	ld c, [hl]
	ld a, 2
	ldh [rSVBK], a
	ld a, c
	ld [de], a
	inc de
	pop hl
	pop bc
	dec b
	jr nz, .field
	ld a, [wPrevDexEntry]
	ld [de], a
	inc de
	ld a, [wPrevDexEntry + 1]
	ld [de], a
	ld a, LOCKED_MON_ID_DEX_SELECTED
	call GetLockedPokemonID
	ld hl, 0
	and a
	call nz, GetPokemonIndexFromID
	ld a, 2
	ldh [rSVBK], a
	ld a, l
	ld [NEW_DEX_REG_LOCK], a
	ld a, h
	ld [NEW_DEX_REG_LOCK + 1], a
	ld a, 1
	ldh [rSVBK], a
	ret

NewDexRegistration_RestoreContext:
	; Restore a lock by permanent identity, never by a recycled transient ID.
	ld a, 2
	ldh [rSVBK], a
	ld a, [NEW_DEX_REG_LOCK]
	ld l, a
	ld a, [NEW_DEX_REG_LOCK + 1]
	ld h, a
	or l
	call nz, GetPokemonIDFromIndex
	ld l, LOCKED_MON_ID_DEX_SELECTED
	call LockPokemonID
	ld a, 2
	ldh [rSVBK], a
	ld hl, wTempTilemap
	ld de, wBattleMenuGFXFlags
	ld bc, $20
	call CopyBytes
	; VRAM and the old producer payload were replaced, so no clean/live claims.
	ld hl, wBattleMenuGFXFlags
	res BATTLE_MENU_GFX_CLEAN_F, [hl]
	xor a
	ld [wBattleFrontpicProducerState], a
	ld [wBattleFrontpicProducerStagedTiles], a
	ld [wBattleFrontpicProducerStageOffset], a
	ld hl, NewDexRegistration_Fields
	ld de, NEW_DEX_REG_FIELDS_AT
	ld b, NEW_DEX_REG_FIELDS
.field
	push bc
	ld a, [hli]
	ld c, a
	ld a, [hli]
	push hl
	ld h, a
	ld l, c
	ld a, [de]
	ld c, a
	ld a, 1
	ldh [rSVBK], a
	ld [hl], c
	ld a, 2
	ldh [rSVBK], a
	inc de
	pop hl
	pop bc
	dec b
	jr nz, .field
	ld a, [de]
	ld [wPrevDexEntry], a
	inc de
	ld a, [de]
	ld [wPrevDexEntry + 1], a
	ld a, 1
	ldh [rSVBK], a
	ret

NewDexRegistration_Fields:
	dw hMapAnims, hSCX, hSCY, hWX, hWY, hVBlank, hOAMUpdate, hBGMapMode
	dw hLCDCPointer, hInMenu, hMapObjectIndex, hObjectStructIndex
	dw wPokedexStatus, wJumptableIndex, wDexArrowCursorPosIndex
	dw wDexArrowCursorDelayCounter, wDexArrowCursorBlinkCounter
	dw wCurPartySpecies, wCurSpecies, wTempSpecies, wUnownLetter
	dw wOptions, wStateFlags, wVolume, wLastVolume, wScriptVar, wMenuCursorY, rVBK
	dw wPayDayMoney, wPayDayMoney + 1, wPayDayMoney + 2
.end
ASSERT (.end - NewDexRegistration_Fields) / 2 == NEW_DEX_REG_FIELDS
