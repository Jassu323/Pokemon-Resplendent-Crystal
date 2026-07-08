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
	; Close the Pack window without restoring its pre-Pack tile backup.
	call ExitMenuNoRestore
	call ClearSprites
	farcall UpdateBattleHUDs
	call LoadTilemapToTempTilemap
	call ClearWindowData
	farcall FinishBattleAnim
	and a
	ret
