_ReturnToBattle_UseBall:
	call ClearBGPalettes
	call DisableLCD
	call ClearSprites
	call hTransferShadowOAM
	call ClearTilemap
	call ExitMenu
	ld a, [wBattleType]
	cp BATTLETYPE_TUTORIAL
	jr z, .gettutorialbackpic
	farcall GetBattleMonBackpic
	jr .continue

.gettutorialbackpic
	farcall GetTrainerBackpic
.continue
	farcall GetEnemyMonFrontpic
	farcall _LoadBattleFontsHPBar
	call GetMemSGBLayout
	call LoadStandardMenuHeader
	call EnableLCD
	call WaitBGMap
	jp SetDefaultBGPAndOBP
