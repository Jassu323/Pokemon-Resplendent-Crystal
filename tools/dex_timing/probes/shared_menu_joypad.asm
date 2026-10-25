; Diagnostic replacement copied into an isolated checkout by shared_input.py.
JoyTextDelay::
	call GetJoypad
	ldh a, [hInMenu]
	and a
	ldh a, [hJoyPressed]
	jr z, .ok
	and PAD_CTRL_PAD
	jr z, .held
	push bc
	ld b, a
	ldh a, [hJoyDown]
	and PAD_BUTTONS
	or b
	pop bc
	jr .ok
.held
	ldh a, [hJoyDown]
.ok
	ldh [hJoyLast], a
	ldh a, [hJoyPressed]
	and a
	jr z, .checkframedelay
	ld a, 15
	ld [wTextDelayFrames], a
	ret

.checkframedelay
	ld a, [wTextDelayFrames]
	and a
	jr z, .restartframedelay
	xor a
	ldh [hJoyLast], a
	ret

.restartframedelay
	ld a, 5
	ld [wTextDelayFrames], a
	ret
