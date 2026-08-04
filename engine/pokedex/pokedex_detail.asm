PokedexDetail_Enter:
	call LowVolume
	xor a
	ld [wPokedexDetailView], a
	ld [wPokedexDetailPendingAction], a
	ld [wPokedexStatus], a ; description page 1
	ld a, DEXDETAIL_STATE_ENTERING
	ld [wPokedexDetailState], a
	ld a, [wPrevDexEntryJumptableIndex]
	ld [wPokedexDetailReturnState], a
	ld hl, wPokedexDetailGeneration
	inc [hl]
	xor a
	ldh [hBGMapMode], a
	call ClearSprites
	farcall Pokedex_LoadCurrentFootprint
	farcall Pokedex_DrawDexEntryScreenBG
	farcall Pokedex_InitArrowCursor
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	ld [wPokedexDetailSpecies], a
	ld a, l
	ld [wPrevDexEntry], a
	ld a, h
	ld [wPrevDexEntry + 1], a
	farcall DisplayDexEntry
	farcall Pokedex_DrawResidentFootprint
	call WaitBGMap
	ld a, $a7
	ldh [hWX], a
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	farcall Pokedex_GetDexSGBLayout
	xor a
	ldh [hBGMapMode], a
	call Pokedex_BeginDescriptionAnimation
	call DelayFrame
	ldh a, [hCGB]
	and a
	jr z, .dmg_cry
	call Pokedex_ServiceAnimationProducer
	call Pokedex_UpdateDescriptionAnimation
	jr .done
.dmg_cry
	ld a, [wCurPartySpecies]
	call PlayMonCry2
.done
	ld a, DEXDETAIL_STATE_ACTIVE
	ld [wPokedexDetailState], a
	farcall Pokedex_IncrementDexPointer
	ret

PokedexDetail_Update:
	call Pokedex_ServiceAnimationProducer
	call Pokedex_UpdateDescriptionAnimation
	farcall PokedexDetail_MoveArrowCursor
	ld hl, hJoyPressed
	ld a, [hl]
	and PAD_B
	jr nz, .return_to_prev_screen
	vc_hook Forbid_printing_Pokedex
	ld a, [hl]
	and PAD_A
	jr nz, .do_menu_action
	farcall Pokedex_NextOrPreviousDexEntry
	ret nc
	farcall Pokedex_IncrementDexPointer
	ret

.do_menu_action
	ld a, [wDexArrowCursorPosIndex]
	ld hl, DexEntryScreen_MenuActionJumptable
	call PokedexDetail_LoadPointer
	jp hl

.return_to_prev_screen
	ld a, DEXDETAIL_STATE_LEAVING
	ld [wPokedexDetailState], a
	call Pokedex_StopDescriptionAnimation
	ld a, [wLastVolume]
	and a
	jr z, .max_volume
	ld a, NORMAL_MAX_VOLUME
	ld [wLastVolume], a

.max_volume
	call MaxVolume
	ld a, [wPokedexDetailReturnState]
	cp DEXSTATE_MAIN_SCR
	jr nz, .set_return_state
	farcall Pokedex_NormalizeListingAfterDetail
.set_return_state
	ld a, [wPokedexDetailReturnState]
	ld [wJumptableIndex], a
	ret

PokedexDetail_Page:
	ld a, [wPokedexStatus]
	xor 1
	ld [wPokedexStatus], a
	farcall Pokedex_GetSelectedMon
	ld a, l
	ld [wPrevDexEntry], a
	ld a, h
	ld [wPrevDexEntry + 1], a
	farcall DisplayDexEntry
	call WaitBGMap
	xor a
	ldh [hBGMapMode], a
	ret

PokedexDetail_SwitchSpecies:
; Reinitialize the Detail view after changing the selected mon.
	ld a, DEXDETAIL_STATE_SWITCHING
	ld [wPokedexDetailState], a
	xor a
	ld [wPokedexDetailPendingAction], a
	ld hl, wPokedexDetailGeneration
	inc [hl]
	call Pokedex_StopDescriptionAnimation
	farcall Pokedex_BlackOutBG
	xor a
	ld [wPokedexStatus], a ; description page 1
	ldh [hBGMapMode], a
	farcall Pokedex_DrawDexEntryScreenBG
	farcall Pokedex_InitArrowCursor
	farcall Pokedex_LoadCurrentFootprint
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	ld [wPokedexDetailSpecies], a
	ld a, l
	ld [wPrevDexEntry], a
	ld a, h
	ld [wPrevDexEntry + 1], a
	farcall DisplayDexEntry
	farcall Pokedex_DrawResidentFootprint
	farcall Pokedex_LoadSelectedMonTiles
	call WaitBGMap
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	farcall Pokedex_GetDexSGBLayout
	xor a
	ldh [hBGMapMode], a
	call Pokedex_StartAnimationPrefetch
	call Pokedex_BeginDescriptionAnimation
	call DelayFrame
	ldh a, [hCGB]
	and a
	jr z, .dmg_cry
	call Pokedex_ServiceAnimationProducer
	call Pokedex_UpdateDescriptionAnimation
	jr .done
.dmg_cry
	ld a, [wCurPartySpecies]
	call PlayMonCry2
.done
	ld a, DEXDETAIL_STATE_ACTIVE
	ld [wPokedexDetailState], a
	ld hl, wJumptableIndex
	dec [hl]
	ret

DexEntryScreen_MenuActionJumptable:
	dw PokedexDetail_Page
	dw PokedexDetail_Area
	dw PokedexDetail_Cry

PokedexDetail_Area:
	call Pokedex_StopDescriptionAnimation
	farcall Pokedex_BlackOutBG
	xor a
	ldh [hSCX], a
	call DelayFrame
	ld a, $7
	ldh [hWX], a
	ld a, $90
	ldh [hWY], a
	farcall Pokedex_GetSelectedMon
	ld a, [wDexCurLocation]
	ld e, a
	predef Pokedex_GetArea
	farcall Pokedex_BlackOutBG
	call DelayFrame
	xor a
	ldh [hBGMapMode], a
	ld a, $90
	ldh [hWY], a
	ld a, POKEDEX_SCX
	ldh [hSCX], a
	call DelayFrame
	call PokedexDetail_Redisplay
	farcall Pokedex_LoadSelectedMonTiles
	call WaitBGMap
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	farcall Pokedex_GetDexSGBLayout
	xor a
	ldh [hBGMapMode], a
	ret

PokedexDetail_Cry:
; BUG: Playing Entei's Pokedex cry can distort Raikou's and Suicune's (see docs/bugs_and_glitches.md)
	farcall Pokedex_GetSelectedMon
	ld a, [wTempSpecies]
	call GetCryIndex
	ld e, c
	ld d, b
	call PlayCry
	ret

PokedexDetail_Redisplay:
	farcall Pokedex_DrawDexEntryScreenBG
	farcall Pokedex_GetSelectedMon
	farcall DisplayDexEntry
	farcall Pokedex_DrawResidentFootprint
	ret

PokedexDetail_LoadPointer:
	ld e, a
	ld d, 0
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret
