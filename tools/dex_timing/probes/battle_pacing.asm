; PRIVATE PACING PROTOTYPE. This file is copied into the isolated candidate.
; It gates the entire logical update; no motion function or frameset is retimed.
; Records are extra holds / logical updates, optional update limit, phase ID.

BattleAnimPacing_Reset:
	ld hl, wBattleAnimPaceExtra
	ld b, wBattleAnimPaceEnd - wBattleAnimPaceExtra
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ret

BattleAnimPacing_SetPhase:
	call GetBattleAnimByte
	ld [wBattleAnimPaceExtra], a
	call GetBattleAnimByte
	ld [wBattleAnimPaceDenominator], a
	call GetBattleAnimByte
	ld [wBattleAnimPaceRemaining], a
; INSTRUMENTATION: this tag identifies the phase in native observer traces.
	call GetBattleAnimByte
	ld [wBattleAnimPacePhase], a
	xor a
	ld [wBattleAnimPaceError], a
	ldh a, [hVBlankCounter]
	ld [wBattleAnimPaceDeadline], a
	ret

BattleAnimPacing_DelayFrame:
	ld a, [wBattleAnimPaceExtra]
	and a
	jp z, BattleAnimDelayFrame
	ld b, a
	ld a, [wBattleAnimPaceError]
	add b
	ld c, a
	ld a, [wBattleAnimPaceDenominator]
	ld b, a
	ld a, c
	ld c, 1
	cp b
	jr c, .no_extra
	sub b
	inc c
.no_extra
	ld [wBattleAnimPaceError], a
	ld a, [wBattleAnimPaceDeadline]
	add c
	ld [wBattleAnimPaceDeadline], a
	call BattleAnimDelayFrame

BattleAnimPacing_CheckDeadline:
	ld a, [wBattleAnimPaceDeadline]
	ld b, a
	ldh a, [hVBlankCounter]
	ld c, a
	ld a, b
	sub c
	jr z, BattleAnimPacing_Finished
	bit 7, a
	jr nz, BattleAnimPacing_Late

BattleAnimPacing_Hold:
; INSTRUMENTATION: count only deliberate additional physical display waits.
	ld hl, wBattleAnimPaceHolds
	inc [hl]
	jr nz, .counted
	inc hl
	inc [hl]
.counted
	call BattleAnimDelayFrame
	jr BattleAnimPacing_CheckDeadline

BattleAnimPacing_Late:
; INSTRUMENTATION: a late update must not be hidden by skipped logical states.
	ld hl, wBattleAnimPaceLate
	inc [hl]
	jr nz, BattleAnimPacing_Finished
	inc hl
	inc [hl]

BattleAnimPacing_Finished:
	ld a, [wBattleAnimPaceRemaining]
	and a
	ret z
	dec a
	ld [wBattleAnimPaceRemaining], a
	ret nz
	xor a
	ld [wBattleAnimPaceExtra], a
	ld [wBattleAnimPacePhase], a
	ret
