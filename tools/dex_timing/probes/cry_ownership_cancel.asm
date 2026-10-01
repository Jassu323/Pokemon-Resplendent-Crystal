; DIAGNOSTIC PROTOTYPE ONLY. Not included by the production build.
; cry_ownership.py supplies linked addresses and overlays the assembled bytes
; into unused space of a private ROM copy. Callers are mainline, IME-enabled
; Selected-Mon owner boundaries. Do not call this from an interrupt handler.

SECTION "Diagnostic Dex Cry Cancellation", ROMX[$7666], BANK[$a0]

PrototypeChange:
	ld a, 2
	ld [wPokedexSelectedState], a
	call PrototypeCancelCry
	ret

PrototypeLeave:
	ld a, 5
	ld [wPokedexSelectedState], a
	call PrototypeCancelCry
	ret

PrototypeArea:
	ld a, 3
	ld [wPokedexSelectedState], a
	call PrototypeCancelCry
	ret

PrototypeCancelCry:
	push af
	push bc
	push de
	push hl
	di
	ldh a, [hSampledCryTimer]
	and a
	call nz, StopSampledCryAsync_NoInterruptControl

	ld b, 0
	ld a, [wChannel5Flags1]
	and $21 ; active channel AND synthesized cry, not stale cry flags
	cp $21
	jr nz, .channel6
	inc b
	xor a
	ld [wChannel5Flags1], a
	ld [wPitchSweep], a
	ldh [$ff10], a
	ldh [$ff12], a
.channel6
	ld a, [wChannel6Flags1]
	and $21
	cp $21
	jr nz, .channel7
	inc b
	xor a
	ld [wChannel6Flags1], a
	ldh [$ff17], a
.channel7
	ld a, [wChannel7Flags1]
	and $21
	cp $21
	jr nz, .channel8
	inc b
	xor a
	ld [wChannel7Flags1], a
	ldh [$ff1a], a
.channel8
	ld a, [wChannel8Flags1]
	and $21
	cp $21
	jr nz, .restore
	inc b
	xor a
	ld [wChannel8Flags1], a
	ldh [$ff21], a
.restore
	ld a, b
	and a
	jr z, .done
	ld a, [wLastVolume]
	and a
	jr z, .clear_priority
	ld [wVolume], a
.clear_priority
	xor a
	ld [wLastVolume], a
	ld [wSFXPriority], a
	ld hl, wChannel6PitchOffset
	ld [hli], a
	ld [hl], a
	ld hl, wChannel8PitchOffset
	ld [hli], a
	ld [hl], a
.done
	pop hl
	pop de
	pop bc
	pop af
	ei
PrototypeCancelCryReturn:
	ret
PrototypeEnd:
