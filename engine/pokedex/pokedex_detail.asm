PokedexSelectedMon_Enter:
	call PokedexSelectedMon_InitializeIcons
	xor a
	ld [wPokedexSelectedView], a
	ld [wPokedexDescriptionPage], a
	ld [wPokedexStatus], a
	ld a, DEXSELECT_STATE_ENTERING
	ld [wPokedexSelectedState], a
	ld a, [wPrevDexEntryJumptableIndex]
	ld [wPokedexSelectedReturnState], a
	cp DEXSTATE_SEARCH_RESULTS_SCR
	call z, PokedexSelectedMon_MarkSearchOrderSeen
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
	jr z, .directions
	call PokedexSelectedMon_ActivateFooterView
	jr .service
.directions
	call PokedexSelectedMon_FindNextSeen
	jp c, PokedexSelectedMon_ChangeSpecies
.service
	call Pokedex_PrepareDescriptionAnimation
	call Pokedex_ServiceAnimationProducer
	call Pokedex_CommitDescriptionAnimation
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_MOVES
	jr nz, .not_moves
	farcall PokedexMoves_Service
	ret
.not_moves
	cp DEXSELECT_VIEW_INFO
	jp nz, PokedexSelectedMon_ServiceDescriptionText
	farcall PokedexInfo_Service
	ret

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
	dw PokedexSelectedMon_Info
	dw PokedexSelectedMon_Moves
	dw PokedexSelectedMon_Area

PokedexSelectedMon_Unavailable:
	ret

PokedexSelectedMon_Info:
	call PokedexSelectedMon_CancelDescriptionText
	farcall PokedexInfo_Activate
	ret

PokedexSelectedMon_Moves:
	call PokedexSelectedMon_CancelDescriptionText
	farcall PokedexMoves_Activate
	ret

PokedexSelectedMon_ToggleDescriptionPage:
	call PokedexSelectedMon_CancelDescriptionText
	ld a, [wPokedexSelectedView]
	and a
	jr z, .description
	farcall PokedexInfo_ReturnDescription
	jr .queue_description
.description
	ld a, [wPokedexDescriptionPage]
	xor 1
	ld [wPokedexDescriptionPage], a
	ld [wPokedexStatus], a
.queue_description
	ldh a, [hCGB]
	and a
	jr z, .dmg
	ld a, [wPokedexSelectedSpecies]
	call CheckCaughtMon
	ret z
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexDescriptionTextState)
	ldh [rSVBK], a
	ld a, POKEDEX_DESCRIPTION_TEXT_INITIALIZE
	ld [wPokedexDescriptionTextState], a
	pop af
	ldh [rSVBK], a
.queued
	ret
.dmg
	xor a
	ldh [hBGMapMode], a
	farcall Pokedex_GetSelectedMon
	ld a, l
	ld [wPrevDexEntry], a
	ld a, h
	ld [wPrevDexEntry + 1], a
	farcall Pokedex_DisplayDescriptionEntry
	farcall Pokedex_CopyBackingToBG
	xor a
	ldh [hBGMapMode], a
	ret

PokedexSelectedMon_ChangeSpecies:
	call PokedexSelectedMon_CancelDescriptionText
	farcall PokedexInfo_Cancel
	ld a, DEXSELECT_STATE_SWITCHING_SPECIES
	ld [wPokedexSelectedState], a
	call PokedexSelectedMon_CancelCry
	ld hl, wPokedexSelectedGeneration
	inc [hl]
	call Pokedex_CancelAnimationPrefetch
	ldh a, [hCGB]
	and a
	jr z, .hide_dmg
	call PokedexSelectedMon_BeginBufferedIconTransition
	jr .transition_ready
.hide_dmg
	call PokedexSelectedMon_BeginHiddenTransition
.transition_ready
	ld hl, wPokedexSelectedPendingIndex
	ld a, [hli]
	ld [wPokedexSelectedIndex], a
	ld a, [hl]
	ld [wPokedexSelectedIndex + 1], a
	xor a
	ld [wPokedexDescriptionPage], a
	ld [wPokedexStatus], a
	call PokedexSelectedMon_StageDescription
	jr c, .revealed
	call PokedexSelectedMon_Reveal
.revealed
	call Pokedex_BeginDescriptionAnimation
	ld a, DEXSELECT_STATE_ACTIVE
	ld [wPokedexSelectedState], a
	ret

PokedexSelectedMon_Leave:
	call PokedexSelectedMon_CancelDescriptionText
	farcall PokedexInfo_Cancel
	ld a, DEXSELECT_STATE_LEAVING
	ld [wPokedexSelectedState], a
	call PokedexSelectedMon_CancelCry
	call Pokedex_CancelAnimationPrefetch
	ld a, [wPokedexListingPresentation]
	and a
	jr nz, .listing_cache_ready
	farcall PokedexInfo_PreserveReturnPanel
	farcall PokedexInfo_RestoreListingCache
.listing_cache_ready
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
	farcall Pokedex_RestoreListingAfterSelectedMon
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
	farcall PokedexPerf_CacheInfoAcrossArea
	call PokedexSelectedMon_CancelDescriptionText
	ld a, [wPokedexSelectedView]
	push af
	farcall PokedexInfo_Cancel
	ld a, DEXSELECT_STATE_SWITCHING_VIEW
	ld [wPokedexSelectedState], a
	call PokedexSelectedMon_CancelCry
	ld a, DEXSELECT_VIEW_AREA
	ld [wPokedexSelectedView], a
	ld hl, wPokedexSelectedGeneration
	inc [hl]
	call Pokedex_CancelAnimationPrefetch
	; Area uses ordinary tile requests, not Selected's publication dispatcher.
	xor a
	ldh [hVBlank], a
	call PokedexSelectedMon_BeginHiddenTransition
	xor a
	ldh [hSCX], a
	ldh [hSCY], a
	ldh [rVBK], a
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

.map_returned
	pop af
	ld [wPokedexSelectedView], a
	call PokedexSelectedMon_BeginHiddenTransition
	ld a, $90
	ldh [hWY], a
	ld a, POKEDEX_SCX
	ldh [hSCX], a
	call PokedexSelectedMon_StageDescription
	call PokedexSelectedMon_Reveal
.restored
	ld a, DEXSELECT_STATE_ACTIVE
	ld [wPokedexSelectedState], a
	ret

PokedexSelectedMon_StageDescription:
	call PokedexSelectedMon_CancelDescriptionText
	xor a
	ldh [hBGMapMode], a
	farcall Pokedex_DrawDescriptionScreenBG
	farcall Pokedex_InitArrowCursor
	ld a, [wPokedexSelectedView]
	and a
	jr z, .footer_ready
	ld [wDexArrowCursorPosIndex], a
.footer_ready
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
	farcall Pokedex_DisplayDescriptionEntry
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
	farcall Pokedex_PrepareSelectedMonTiles
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_SWITCHING_SPECIES
	call z, PokedexSelectedMon_BeginHiddenTransition
	farcall Pokedex_CommitPreparedSelectedMonGFX
	jr .selected_tiles_ready

.load_selected_tiles_dmg
	farcall Pokedex_LoadSelectedMonTiles
.selected_tiles_ready
	call PokedexSelectedMon_DrawFootprint
	farcall Pokedex_LoadDescriptionTypeGFX
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_AREA_ACTIVE
	jr nz, .prepare_animation
	; The base loader arms a producer; Area return needs only the static portrait.
	call Pokedex_CancelAnimationPrefetch
	jr .animation_ready
.prepare_animation
	call Pokedex_StartAnimationPrefetch
	call Pokedex_PrimeDescriptionAnimation
.animation_ready
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	ldh a, [hCGB]
	and a
	jr z, .sgb_layout
	farcall CGB_PokedexStageSelectedMonLayout
	call PokedexSelectedMon_StageUsualPals
	farcall PokedexInfo_StageTypePalettes
	farcall PokedexInfo_StageStaticPalettes
	farcall PokedexInfo_PrepareSpecies
	xor a
	ldh [hCGBPalUpdate], a
	call Pokedex_StageInitialAnimationFrame
	jr .copy_backing

.sgb_layout
	farcall Pokedex_GetDexSGBLayout
.copy_backing
	farcall Pokedex_PublishOrStageDescriptionBacking
	ret

PokedexSelectedMon_StageUsualPals:
; ApplyPals already copied the identity BG mapping. Retain the usual OBJ0
; conversion without requesting publication before the owner maps are ready.
	ld a, $e4
	ldh [rBGP], a
	ld a, $e0
	ldh [rOBP0], a
	ldh a, [rSVBK]
	push af
	ld a, BANK(wOBPals2)
	ldh [rSVBK], a
	ld hl, wOBPals2
	ld de, wOBPals1
	ld b, $e0
	ld c, 1
	call CopyPals
	pop af
	ldh [rSVBK], a
	ret

PokedexSelectedMon_BeginHiddenTransition:
	xor a
	ldh [hBGMapMode], a
	ldh a, [hCGB]
	and a
	jr z, .clear_sprites
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_SWITCHING_SPECIES
	jr nz, .clear_sprites
; The outgoing badges and Info sprites remain visible until the owner reveal.
	ld a, TRUE
	ldh [hOAMUpdate], a
	farcall Pokedex_BlackOutSelectedMonBG
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	call DelayFrame
	ret
.clear_sprites
	call ClearSprites
	xor a
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

PokedexSelectedMon_InitializeIcons:
	farcall PokedexInfo_Reset
	xor a
	ld [POKEDEX_DESCRIPTION_ICON_BUFFER], a
	jp LowVolume

PokedexSelectedMon_BeginBufferedIconTransition:
; Choose the inactive set before StageDescription replaces the backing map.
	hlcoord 18, 1
	ld a, [hl]
	cp POKEDEX_RESIDENT_FOOTPRINT_TILE
	ld a, 0
	jr nz, .store
	inc a
.store
	ld [POKEDEX_DESCRIPTION_ICON_BUFFER], a
	jp PokedexSelectedMon_BeginWarmTransition

PokedexSelectedMon_DrawFootprint:
	ldh a, [hCGB]
	and a
	jr nz, .cgb
	farcall Pokedex_DrawResidentFootprint
	ret
.cgb
	ld a, [POKEDEX_DESCRIPTION_ICON_BUFFER]
	and a
	jr nz, .alternate
; Listing may retain the frontpic while its normal footprint cache is invalid.
	ld a, [wPokedexSelectedSpecies]
	ld b, a
	ld a, [wPokedexResidentFootprintSpecies]
	cp b
	jr z, .original
	farcall Pokedex_ReloadNormalFootprint
.original
	ld a, POKEDEX_RESIDENT_FOOTPRINT_TILE
	jr .place
.alternate
	ld a, POKEDEX_DESCRIPTION_ALT_FOOTPRINT_TILE
.place
	hlcoord 18, 1
	ld [hli], a
	inc a
	ld [hl], a
	inc a
	hlcoord 18, 2
	ld [hli], a
	inc a
	ld [hl], a
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

PokedexSelectedMon_MarkSearchOrderSeen:
; Search results are compacted from seen Pokemon, so every valid order
; position is eligible for Selected-page paging.
	ld hl, POKEDEX_ORDER_SEEN_FLAGS
	ld bc, POKEDEX_ORDER_SEEN_BYTES
	ld a, $ff
	jp ByteFill

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
	jr c, .next_in_range
	ld hl, 0
.next_in_range
	call .IsCurrentIndex
	ret z
	call .IndexIsSeen
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
	jr nz, .previous_in_range
	ld hl, wDexListingEnd
	ld a, [hli]
	ld h, [hl]
	ld l, a
.previous_in_range
	dec hl
	call .IsCurrentIndex
	ret z
	call .IndexIsSeen
	jr z, .previous_loop

.found
	ld a, l
	ld [wPokedexSelectedPendingIndex], a
	ld a, h
	ld [wPokedexSelectedPendingIndex + 1], a
	scf
	ret

.IsCurrentIndex:
	ld a, [wPokedexSelectedIndex]
	cp l
	ret nz
	ld a, [wPokedexSelectedIndex + 1]
	cp h
	ret

.IndexIsSeen:
	push hl
	ld d, h
	ld e, l
	ld hl, POKEDEX_ORDER_SEEN_FLAGS
	ld b, CHECK_FLAG
	call FlagAction
	pop hl
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

PokedexSelectedMon_CancelCry:
; Accepted Selected Mon ownership changes only; callers have IME enabled.
	push af
	push bc
	push de
	push hl
	di
	ldh a, [hSampledCryTimer]
	and a
	call nz, StopSampledCryAsync_NoInterruptControl
; Stop the sample before muting synth channels, since sample stop restores audio.
	ld b, 0
	ld a, [wChannel5Flags1]
	and (1 << SOUND_CHANNEL_ON) | (1 << SOUND_CRY)
	cp (1 << SOUND_CHANNEL_ON) | (1 << SOUND_CRY)
	jr nz, .channel6
	inc b
	xor a
	ld [wChannel5Flags1], a
	ld [wPitchSweep], a
	ldh [rAUD1SWEEP], a
	ldh [rAUD1ENV], a
.channel6
	ld a, [wChannel6Flags1]
	and (1 << SOUND_CHANNEL_ON) | (1 << SOUND_CRY)
	cp (1 << SOUND_CHANNEL_ON) | (1 << SOUND_CRY)
	jr nz, .channel7
	inc b
	xor a
	ld [wChannel6Flags1], a
	ldh [rAUD2ENV], a
.channel7
	ld a, [wChannel7Flags1]
	and (1 << SOUND_CHANNEL_ON) | (1 << SOUND_CRY)
	cp (1 << SOUND_CHANNEL_ON) | (1 << SOUND_CRY)
	jr nz, .channel8
	inc b
	xor a
	ld [wChannel7Flags1], a
	ldh [rAUD3ENA], a
.channel8
	ld a, [wChannel8Flags1]
	and (1 << SOUND_CHANNEL_ON) | (1 << SOUND_CRY)
	cp (1 << SOUND_CHANNEL_ON) | (1 << SOUND_CRY)
	jr nz, .restore
	inc b
	xor a
	ld [wChannel8Flags1], a
	ldh [rAUD4ENV], a
.restore
	ld a, b
	and a
	jr z, .done
	ld a, [wLastVolume]
	and a
	jr z, .clear_priority
	ld [wVolume], a
.clear_priority
	xor a
	ld [wLastVolume], a
	ld [wSFXPriority], a
	ld hl, wChannel6PitchOffset
	ld [hli], a
	ld [hl], a
	ld hl, wChannel8PitchOffset
	ld [hli], a
	ld [hl], a
.done
	pop hl
	pop de
	pop bc
	pop af
	ei
.return
	ret
.end
