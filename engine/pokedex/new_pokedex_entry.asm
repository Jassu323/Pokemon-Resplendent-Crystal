NewPokedexEntry:
	ldh a, [hMapAnims]
	push af
	xor a
	ldh [hMapAnims], a
	call LowVolume
	call ClearBGPalettes
	call ClearTilemap
	call UpdateSprites
	call ClearSprites
	ld a, [wPokedexStatus]
	push af
	ldh a, [hSCX]
	add POKEDEX_SCX
	ldh [hSCX], a
	xor a
	ld [wPokedexStatus], a
	farcall _NewPokedexEntry
	call .WaitPressAorB_AnimateFrontpic
	ld a, 1 ; page 2
	ld [wPokedexStatus], a
	farcall DisplayDexEntry
	call WaitBGMap
	call .WaitPressAorB_AnimateFrontpic
	xor a
	ld [wFrameCounter], a
	pop af
	ld [wPokedexStatus], a
	call MaxVolume
	call RotateThreePalettesRight
	ldh a, [hSCX]
	add -POKEDEX_SCX
	ldh [hSCX], a
	call .ReturnFromDexRegistration
	pop af
	ldh [hMapAnims], a
	ret

.ReturnFromDexRegistration:
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

.WaitPressAorB_AnimateFrontpic:
	ldh a, [hMapObjectIndex]
	push af
	ldh a, [hObjectStructIndex]
	push af
	xor a
	ldh [hMapObjectIndex], a
	ld a, 6
	ldh [hObjectStructIndex], a

.wait_loop
	ld a, [wFrameCounter]
	and a
	jr z, .delay_frame
	call .AnimateFrontpicFrame
	jr .frame_done

.delay_frame
	call DelayFrame

.frame_done
	push hl
	hlcoord 18, 17
	call BlinkCursor
	pop hl
	call JoyTextDelay
	ldh a, [hJoyLast]
	and PAD_A | PAD_B
	jr z, .wait_loop

	pop af
	ldh [hObjectStructIndex], a
	pop af
	ldh [hMapObjectIndex], a
	ret

.AnimateFrontpicFrame:
	ld a, [wFrameCounter]
	and a
	ret z
	farcall SetUpPokeAnim
	jr nc, .transfer
	xor a
	ld [wFrameCounter], a

.transfer
	farcall HDMATransferTilemapToWRAMBank3
	ret
