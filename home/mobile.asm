SampledCryTimer::
	push af
	ldh a, [hSampledCryTimer]
; Active value 1 takes the original normal/even-period IRQ budget.
	dec a
	jr z, .sampled_cry_timer
	inc a
	jr z, .inactive
	push bc
	push de
	push hl
	call SampledCry_AsyncTimerTickAlternating
	jr .restore
.inactive
	pop af
	reti

.sampled_cry_timer
	push bc
	push de
	push hl

	call SampledCry_AsyncTimerTick

.restore
	pop hl
	pop de
	pop bc
	pop af
	reti

MobileAPI::
	ld a, $ff
	ld hl, 0
	scf
	ret

ReturnMobileAPI::
	ret

MobileReceive::
	ret

MobileTimer::
	reti

Function3eea::
Function3f20::
Function3f35::
MobileHome_PlaceBox:
Function3f7c::
Function3f88::
Function3f9f::
	ret
