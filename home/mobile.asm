SampledCryTimer::
	push af
	ldh a, [hSampledCryTimer]
	and a
	jr nz, .sampled_cry_timer
	pop af
	reti

.sampled_cry_timer
	push bc
	push de
	push hl

	call SampledCry_AsyncTimerTick

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
