; Successful-capture tail only, after WaitSFX and MUSIC_NONE.
; Do not reuse for double-to-normal switching or active battle animations.
BattleSpeed_CaptureHandoff::
	ld a, [wBattleType]
	cp BATTLETYPE_TUTORIAL
	ret z
	ldh a, [rKEY1]
	bit 7, a
	ret nz
	push bc
	push de
	push hl
	call .SwitchWithoutBlank
	pop hl
	pop de
	pop bc
	ret

.SwitchWithoutBlank:
	ldh a, [rLCDC]
	bit 7, a
	jp z, BattleSpeed_LeaveNormal
	di
	ldh a, [rIE]
	push af
	ldh a, [hSampledCryTimer]
	and a
	call nz, StopSampledCryAsync_NoInterruptControl
	xor a
	ldh [rNR52], a
	ldh [rIF], a
	ldh [rIE], a
	ld a, JOYP_GET_NONE
	ldh [rJOYP], a
	ldh a, [rKEY1]
	or 1
	ldh [rKEY1], a
; Enter STOP just after the next mode-2 -> mode-3 edge. Starting in mode
; 0/1 can black out pixels; starting in mode 2 can hide sprites (Pan Docs).
.WaitOAM
	ldh a, [rSTAT]
	and 3
	cp 2
	jr nz, .WaitOAM
.WaitRendering
	ldh a, [rSTAT]
	and 3
	cp 3
	jr nz, .WaitRendering
.SwitchNow
	stop
.Resumed
	call InitSound
	pop af
	ldh [rIE], a
	ei
	ret
