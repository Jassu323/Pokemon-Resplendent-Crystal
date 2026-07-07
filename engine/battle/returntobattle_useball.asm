_ReturnToBattle_UseBall:
	call ClearBGPalettes
	call DelayFrame
	call ClearSprites
	; Direct OAM DMA from mainline code must not be interrupted.
	di
	call hTransferShadowOAM
	ei
	xor a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	call LoadTempTilemapToTilemap
	call ClearWindowData
	farcall CGB_PrepareBattleScreenLayoutNoApply
	call GetMemSGBLayout
	call WaitBGMap
	call SetDefaultBGPAndOBP
	ld hl, wBattleMenuGFXFlags
	res BATTLE_MENU_GFX_VISIBLE_F, [hl]
	set BATTLE_MENU_GFX_BALL_RETURN_F, [hl]
	ret

BattleCore_BallReturnCleanup:
	xor a
	ldh [hBGMapMode], a
	call ClearSprites
	farcall UpdateBattleHUDs
	farcall BattleMenuGraphic_BlankLowerArea
	call .UpdateTilemapAndAttrmap
	call WaitBGMap
	call LoadTilemapToTempTilemap
	call ClearWindowData
	farcall FinishBattleAnim
	and a
	ret

.UpdateTilemapAndAttrmap:
	ldh a, [hCGB]
	and a
	ret z
.wait
	ldh a, [rLY]
	cp LY_VBLANK
	jr c, .wait
	cp LY_VBLANK + 2
	jr nc, .wait
	call UpdateCGBPals
	call CGBOnly_CopyTilemapAtOnce
	ret
