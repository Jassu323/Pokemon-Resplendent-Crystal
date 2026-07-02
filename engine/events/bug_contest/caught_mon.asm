BugContest_SetCaughtContestMon:
	call BugContest_GetContestMonSpecies
	and a
	jr z, .firstcatch
	ld [wNamedObjectIndex], a
	farcall DisplayAlreadyCaughtText
	farcall DisplayCaughtContestMonStats
	lb bc, 14, 7
	call PlaceYesNoBox
	ret c

.firstcatch
	call .generatestats
	ld a, [wTempEnemyMonSpecies]
	ld [wNamedObjectIndex], a
	call GetPokemonName
	ld hl, .ContestCaughtMonText
	call PrintText
	ret

.generatestats
	ld a, [wTempEnemyMonSpecies]
	ld [wCurSpecies], a
	ld [wCurPartySpecies], a
	call GetBaseData
	xor a
	ld bc, PARTYMON_STRUCT_LENGTH
	ld hl, wTempMon
	call ByteFill
	xor a
	ld [wMonType], a
	ld hl, wTempMon
	call GeneratePartyMonStats
	jp BugContest_CopyTempMonToContestMon

.ContestCaughtMonText:
	text_far _ContestCaughtMonText
	text_end

BugContest_ClearContestMon::
	ldh a, [rSVBK]
	push af
	ld a, BANK(wContestMon)
	ldh [rSVBK], a
	xor a
	ld hl, wContestMon
	ld bc, PARTYMON_STRUCT_LENGTH
	call ByteFill
	pop af
	ldh [rSVBK], a
	ret

BugContest_GetContestMonSpecies::
	ld de, wContestMonSpecies
	jr BugContest_GetContestMonByte

BugContest_GetContestMonLevel::
	ld de, wContestMonLevel

BugContest_GetContestMonByte:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wContestMon)
	ldh [rSVBK], a
	ld a, [de]
	ld c, a
	pop af
	ldh [rSVBK], a
	ld a, c
	ret

BugContest_CopyTempMonToContestMon::
	ld hl, wTempMon
	ld de, wContestMon
	ld c, PARTYMON_STRUCT_LENGTH
	ldh a, [rSVBK]
	push af
.loop
	ld a, BANK(wTempMon)
	ldh [rSVBK], a
	ld b, [hl]
	inc hl
	ld a, BANK(wContestMon)
	ldh [rSVBK], a
	ld a, b
	ld [de], a
	inc de
	dec c
	jr nz, .loop
	pop af
	ldh [rSVBK], a
	ret

BugContest_CopyContestMonToTempMon::
	ld de, wTempMon
	ld c, PARTYMON_STRUCT_LENGTH
	jr BugContest_CopyContestMonToDE

BugContest_CopyContestMonToDE::
; Copy c bytes from moved wContestMon to the WRAMX1 destination in de.
	ld hl, wContestMon
	ldh a, [rSVBK]
	push af
.loop
	ld a, BANK(wContestMon)
	ldh [rSVBK], a
	ld b, [hl]
	inc hl
	ld a, BANK(wTempMon) ; WRAMX1
	ldh [rSVBK], a
	ld a, b
	ld [de], a
	inc de
	dec c
	jr nz, .loop
	pop af
	ldh [rSVBK], a
	ret
