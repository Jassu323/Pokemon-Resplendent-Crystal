PokedexSelectedMon_Enter:
	call LowVolume
	xor a
	ld [wPokedexSelectedView], a
	ld [wPokedexDescriptionPage], a
	ld [wPokedexStatus], a
	ld a, DEXSELECT_STATE_ENTERING
	ld [wPokedexSelectedState], a
	ld a, [wPrevDexEntryJumptableIndex]
	ld [wPokedexSelectedReturnState], a
	ld hl, wPokedexSelectedGeneration
	inc [hl]
	farcall Pokedex_SaveListingViewport
	call PokedexSelectedMon_CaptureListingSelection
	ld a, [wPokedexSelectedReturnState]
	cp DEXSTATE_MAIN_SCR
	jr nz, .hidden_transition
	call PokedexSelectedMon_BeginWarmTransition
	jr .transition_ready

.hidden_transition
	call PokedexSelectedMon_BeginHiddenTransition
.transition_ready
	call PokedexSelectedMon_StageDescription
	jr c, .revealed
	call PokedexSelectedMon_Reveal
.revealed
	call Pokedex_BeginDescriptionAnimation
	ld a, DEXSELECT_STATE_ACTIVE
	ld [wPokedexSelectedState], a
	farcall Pokedex_IncrementDexPointer
	ret

PokedexSelectedMon_Update:
	farcall PokedexSelectedMon_ReadFooterCursor
	push af
	call PokedexSelectedMon_CommitFooterCursor
	pop af
	ld hl, hJoyPressed
	ld a, [hl]
	and PAD_B
	jp nz, PokedexSelectedMon_Leave
	ld a, [hl]
	and PAD_A
	jp nz, PokedexSelectedMon_ActivateFooterView
	call PokedexSelectedMon_FindNextSeen
	jp c, PokedexSelectedMon_ChangeSpecies
	call Pokedex_ServiceAnimationProducer
	jp Pokedex_UpdateDescriptionAnimation

PokedexSelectedMon_CommitFooterCursor:
	xor a
	ldh [hBGMapMode], a
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	hlcoord 1, 17
	debgcoord 1, 17
	call PokedexSelectedMon_CopyBackingTileToVRAM
	hlcoord 6, 17
	debgcoord 6, 17
	call PokedexSelectedMon_CopyBackingTileToVRAM
	hlcoord 11, 17
	debgcoord 11, 17
	call PokedexSelectedMon_CopyBackingTileToVRAM
	hlcoord 15, 17
	debgcoord 15, 17
	call PokedexSelectedMon_CopyBackingTileToVRAM
	pop af
	ldh [rVBK], a
	ret

PokedexSelectedMon_CopyBackingTileToVRAM:
.wait_vram
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_vram
	ld a, [hl]
	ld [de], a
	ret

PokedexSelectedMon_ActivateFooterView:
	ld a, [wDexArrowCursorPosIndex]
	ld hl, PokedexSelectedMon_ViewActionJumptable
	call PokedexSelectedMon_LoadPointer
	jp hl

PokedexSelectedMon_ViewActionJumptable:
	dw PokedexSelectedMon_ToggleDescriptionPage
	dw PokedexSelectedMon_Unavailable
	dw PokedexSelectedMon_Unavailable
	dw PokedexSelectedMon_Area

PokedexSelectedMon_Unavailable:
	ret

PokedexSelectedMon_ToggleDescriptionPage:
	ld a, [wPokedexDescriptionPage]
	xor 1
	ld [wPokedexDescriptionPage], a
	ld [wPokedexStatus], a
	xor a
	ldh [hBGMapMode], a
	farcall Pokedex_GetSelectedMon
	ld a, l
	ld [wPrevDexEntry], a
	ld a, h
	ld [wPrevDexEntry + 1], a
	farcall DisplayDexEntry
	farcall Pokedex_CopyBackingToBG
	xor a
	ldh [hBGMapMode], a
	ret

PokedexSelectedMon_ChangeSpecies:
	ld a, DEXSELECT_STATE_SWITCHING_SPECIES
	ld [wPokedexSelectedState], a
	ld hl, wPokedexSelectedGeneration
	inc [hl]
	call Pokedex_CancelAnimationPrefetch
	call PokedexSelectedMon_BeginHiddenTransition
	ld hl, wPokedexSelectedPendingIndex
	ld a, [hli]
	ld [wPokedexSelectedIndex], a
	ld a, [hl]
	ld [wPokedexSelectedIndex + 1], a
	xor a
	ld [wPokedexDescriptionPage], a
	ld [wPokedexStatus], a
	call PokedexSelectedMon_StageDescription
	call PokedexSelectedMon_Reveal
	call Pokedex_BeginDescriptionAnimation
	ld a, DEXSELECT_STATE_ACTIVE
	ld [wPokedexSelectedState], a
	ret

PokedexSelectedMon_Leave:
	ld a, DEXSELECT_STATE_LEAVING
	ld [wPokedexSelectedState], a
	call Pokedex_CancelAnimationPrefetch
	ld a, [wPokedexSelectedReturnState]
	cp DEXSTATE_MAIN_SCR
	jr z, .restore_volume
	call PokedexSelectedMon_BeginHiddenTransition

.restore_volume
	ld a, [wLastVolume]
	and a
	jr z, .max_volume
	ld a, NORMAL_MAX_VOLUME
	ld [wLastVolume], a

.max_volume
	call MaxVolume
	ld a, [wPokedexSelectedReturnState]
	cp DEXSTATE_MAIN_SCR
	jr nz, .linear_return
	farcall Pokedex_NormalizeListingAfterSelectedMon
	jr .set_return_state

.linear_return
	xor a
	ld [wPokedexSelectedState], a
	call PokedexSelectedMon_NormalizeLinearReturn
.set_return_state
	ld a, [wPokedexSelectedReturnState]
	ld [wJumptableIndex], a
	ret

PokedexSelectedMon_Area:
	ld a, DEXSELECT_STATE_SWITCHING_VIEW
	ld [wPokedexSelectedState], a
	ld a, DEXSELECT_VIEW_AREA
	ld [wPokedexSelectedView], a
	ld hl, wPokedexSelectedGeneration
	inc [hl]
	call Pokedex_CancelAnimationPrefetch
	call PokedexSelectedMon_BeginHiddenTransition
	xor a
	ldh [hSCX], a
	ld a, $7
	ldh [hWX], a
	ld a, $90
	ldh [hWY], a
	ld a, DEXSELECT_STATE_AREA_ACTIVE
	ld [wPokedexSelectedState], a
	farcall Pokedex_GetSelectedMon
	ld a, [wDexCurLocation]
	ld e, a
	predef Pokedex_GetArea

	call PokedexSelectedMon_BeginHiddenTransition
	ld a, $90
	ldh [hWY], a
	ld a, POKEDEX_SCX
	ldh [hSCX], a
	ld a, DEXSELECT_VIEW_DESCRIPTION
	ld [wPokedexSelectedView], a
	call PokedexSelectedMon_StageDescription
	call PokedexSelectedMon_Reveal
	call Pokedex_BeginDescriptionAnimation
	ld a, DEXSELECT_STATE_ACTIVE
	ld [wPokedexSelectedState], a
	ret

PokedexSelectedMon_StageDescription:
	xor a
	ldh [hBGMapMode], a
	farcall Pokedex_DrawDexEntryScreenBG
	farcall Pokedex_InitArrowCursor
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	ld [wPokedexSelectedSpecies], a
	ld [wCurPartySpecies], a
	ld a, l
	ld [wPrevDexEntry], a
	ld a, h
	ld [wPrevDexEntry + 1], a
	ld a, [wPokedexDescriptionPage]
	ld [wPokedexStatus], a
	farcall DisplayDexEntry
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_ENTERING
	jr nz, .load_selected_tiles
	ld a, [wPokedexSelectedReturnState]
	cp DEXSTATE_MAIN_SCR
	jr z, .selected_tiles_ready

.load_selected_tiles
	ldh a, [hCGB]
	and a
	jr z, .load_selected_tiles_dmg
	farcall Pokedex_PrepareAndCommitSelectedMonGFX
	jr .selected_tiles_ready

.load_selected_tiles_dmg
	farcall Pokedex_LoadSelectedMonTiles
.selected_tiles_ready
	farcall Pokedex_DrawResidentFootprint
	call Pokedex_StartAnimationPrefetch
	call Pokedex_PrimeDescriptionAnimation
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	ldh a, [hCGB]
	and a
	jr z, .sgb_layout
	farcall CGB_PokedexStageSelectedMonLayout
	farcall Pokedex_ApplyUsualPals
	xor a
	ldh [hCGBPalUpdate], a
	call Pokedex_StageInitialAnimationFrame
	jr .copy_backing

.sgb_layout
	farcall Pokedex_GetDexSGBLayout
.copy_backing
	farcall Pokedex_PublishOrStageDescriptionBacking
	ret

PokedexSelectedMon_BeginHiddenTransition:
	xor a
	ldh [hBGMapMode], a
	call ClearSprites
	ldh [hOAMUpdate], a
	ldh a, [hCGB]
	and a
	jr z, .dmg
	farcall Pokedex_BlackOutSelectedMonBG
	farcall ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	call DelayFrame
	jr .hold_oam

.dmg
	call ClearPalettes
	call DelayFrame

.hold_oam
	ld a, TRUE
	ldh [hOAMUpdate], a
	ret

PokedexSelectedMon_BeginWarmTransition:
; Keep the outgoing owner visible while its replacement is prepared.
	xor a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	ld a, TRUE
	ldh [hOAMUpdate], a
	call ClearSprites
	ret

PokedexSelectedMon_Reveal:
	xor a
	ldh [hBGMapMode], a
	ld a, $a7
	ldh [hWX], a
	ldh a, [hCGB]
	and a
	jr z, .show_oam
	ld a, TRUE
	ldh [hCGBPalUpdate], a
.show_oam
	xor a
	ldh [hOAMUpdate], a
	call DelayFrame
	ret

PokedexSelectedMon_CaptureListingSelection:
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld e, a
	ld d, [hl]
	ld a, [wDexListingCursor]
	add e
	ld e, a
	ld a, d
	adc 0
	ld d, a
	ld a, e
	ld [wPokedexSelectedIndex], a
	ld a, d
	ld [wPokedexSelectedIndex + 1], a
	ret

PokedexSelectedMon_NormalizeLinearReturn:
; Search Results owns a conventional linear viewport. Keep its previous
; viewport when possible and otherwise place the selected entry at an edge.
	ld hl, wPokedexSelectedIndex
	ld a, [hli]
	ld e, a
	ld d, [hl]
	ld hl, wPokedexListingSavedScrollOffset
	ld a, [hli]
	ld c, a
	ld b, [hl]
	ld a, d
	cp b
	jr c, .above_view
	jr nz, .check_below
	ld a, e
	cp c
	jr c, .above_view

.check_below
	ld h, b
	ld l, c
	ld a, [wDexListingHeight]
	add l
	ld l, a
	ld a, h
	adc 0
	ld h, a
	ld a, d
	cp h
	jr c, .use_saved
	jr nz, .below_view
	ld a, e
	cp l
	jr c, .use_saved

.below_view
	ld h, d
	ld l, e
	ld a, [wDexListingHeight]
	dec a
	ld c, a
	ld b, 0
	ld a, l
	sub c
	ld l, a
	ld a, h
	sbc b
	ld h, a
	jr .store_view

.above_view
	ld h, d
	ld l, e
	jr .store_view

.use_saved
	ld h, b
	ld l, c

.store_view
	ld a, l
	ld [wDexListingScrollOffset], a
	ld c, a
	ld a, h
	ld [wDexListingScrollOffset + 1], a
	ld b, a
	ld a, e
	sub c
	ld e, a
	ld a, d
	sbc b
	ld a, e
	ld [wDexListingCursor], a
	ret

PokedexSelectedMon_FindNextSeen:
	ldh a, [hJoyLast]
	and PAD_UP
	jr nz, .previous
	ldh a, [hJoyLast]
	and PAD_DOWN
	ret z

	ld hl, wPokedexSelectedIndex
	ld a, [hli]
	ld h, [hl]
	ld l, a
.next
	inc hl
	call .IndexBeforeEnd
	ret nc
	push hl
	ld d, h
	ld e, l
	farcall Pokedex_GetMonAtOrderIndexDE
	farcall Pokedex_CheckSeen
	pop hl
	jr z, .next
	jr .found

.previous
	ld hl, wPokedexSelectedIndex
	ld a, [hli]
	ld h, [hl]
	ld l, a
.previous_loop
	ld a, h
	or l
	ret z
	dec hl
	push hl
	ld d, h
	ld e, l
	farcall Pokedex_GetMonAtOrderIndexDE
	farcall Pokedex_CheckSeen
	pop hl
	jr z, .previous_loop

.found
	ld a, l
	ld [wPokedexSelectedPendingIndex], a
	ld a, h
	ld [wPokedexSelectedPendingIndex + 1], a
	scf
	ret

.IndexBeforeEnd:
	ld a, [wDexListingEnd]
	ld e, a
	ld a, [wDexListingEnd + 1]
	ld d, a
	ld a, h
	cp d
	jr c, .valid
	ret nz
	ld a, l
	cp e
	ret nc
.valid
	scf
	ret

PokedexSelectedMon_LoadPointer:
	ld e, a
	ld d, 0
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret
