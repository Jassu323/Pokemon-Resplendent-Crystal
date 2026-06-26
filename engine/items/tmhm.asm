ConvertCurItemIntoCurTMHM:
	ld a, [wCurItem]
	ld c, a
	callfar GetTMHMNumber
	ld a, c
	ld [wTempTMHM], a
	ret

GetTMHMItemMove:
	call ConvertCurItemIntoCurTMHM
	predef GetTMHMMove
	ret

AskTeachTMHM:
	ld hl, wOptions
	ld a, [hl]
	push af
	res NO_TEXT_SCROLL, [hl]
	ld a, [wCurItem]
	cp TM01
	jr c, .NotTMHM
	call GetTMHMItemMove
	ld a, [wTempTMHM]
	ld [wPutativeTMHMMove], a
	call GetMoveName
	call CopyName1
	ld hl, BootedTMText ; Booted up a TM
	ld a, [wCurItem]
	cp HM01
	jr c, .TM
	ld hl, BootedHMText ; Booted up an HM
.TM:
	call PrintText
	ld hl, ContainedMoveText
	call PrintText
	call YesNoBox
.NotTMHM:
	pop bc
	ld a, b
	ld [wOptions], a
	ret

ChooseMonToLearnTMHM:
	ld hl, wStringBuffer2
	ld de, wTMHMMoveNameBackup
	ld bc, MOVE_NAME_LENGTH - 1
	call CopyBytes
	call ClearBGPalettes
ChooseMonToLearnTMHM_NoRefresh:
	farcall LoadPartyMenuGFX
	farcall InitPartyMenuWithCancel
	farcall InitPartyMenuGFX
	ld a, PARTYMENUACTION_TEACH_TMHM
	ld [wPartyMenuActionText], a
.loopback
	farcall WritePartyMenuTilemap
	farcall PlacePartyMenuText
	call WaitBGMap
	call SetDefaultBGPAndOBP
	call DelayFrame
	farcall PartyMenuSelect
	push af
	ld a, [wCurPartySpecies]
	cp EGG
	pop bc ; now contains the former contents of af
	jr z, .egg
	push bc
	ld hl, wTMHMMoveNameBackup
	ld de, wStringBuffer2
	ld bc, MOVE_NAME_LENGTH - 1
	call CopyBytes
	pop af ; now contains the original contents of af
	ret

.egg
	push hl
	push de
	push bc
	push af
	ld de, SFX_WRONG
	call PlaySFX
	call WaitSFX
	pop af
	pop bc
	pop de
	pop hl
	jr .loopback

TeachTMHM:
	predef CanLearnTMHMMove

	push bc
	ld a, [wCurPartyMon]
	ld hl, wPartyMonNicknames
	call GetNickname
	pop bc

	ld a, c
	and a
	jr nz, .compatible
	push de
	ld de, SFX_WRONG
	call PlaySFX
	pop de
	ld hl, TMHMNotCompatibleText
	call PrintText
	jr .nope

.compatible
	callfar KnowsMove
	jr c, .nope

	predef LearnMove
	ld a, b
	and a
	jr z, .nope

	farcall StubbedTrainerRankings_TMsHMsTaught
	ld a, [wCurItem]
	call IsHM
	ret c

	ld c, HAPPINESS_LEARNMOVE
	callfar ChangeHappiness
	jr .learned_move

.nope
	and a
	ret

.didnt_use ; unreferenced
	ld a, 2
	ld [wItemEffectSucceeded], a
.learned_move
	scf
	ret

BootedTMText:
	text_far _BootedTMText
	text_end

BootedHMText:
	text_far _BootedHMText
	text_end

ContainedMoveText:
	text_far _ContainedMoveText
	text_end

TMHMNotCompatibleText:
	text_far _TMHMNotCompatibleText
	text_end
