; Host-only cost specification. Never included in a game build or replay ROM.
INCLUDE "direction-cost-symbols.asm"

SECTION "Direction Cost Specification", ROMX[$4000], BANK[1]

DirectionCostBaseline:
	jp JoyTextDelay
DirectionCostBaselineEnd:

DirectionCostAllDex:
	call JoyTextDelay
	ldh a, [hJoyPressed]
	and $f0
	ret z
	ld b, a
	ldh a, [hJoyLast]
	and $0f
	or b
	ldh [hJoyLast], a
	ret
DirectionCostAllDexEnd:

DirectionCostScoped:
	call JoyTextDelay
	ld a, [wJumptableIndex]
	cp 1 ; Listing update
	jr z, .filter
	cp 3 ; Selected update
	jr z, .filter
	cp 4 ; Reserved alias of Selected update
	ret nz
.filter
	ldh a, [hJoyPressed]
	and $f0
	ret z
	ld b, a
	ldh a, [hJoyLast]
	and $0f
	or b
	ldh [hJoyLast], a
	ret
DirectionCostScopedEnd:

; Copies of the shared routine are only for isolated size/contract measurements.
; Both call the real GetJoypad. Neither is linked into the game.
DirectionCostGlobalBaseline:
	call GetJoypad
	ldh a, [hInMenu]
	and a
	ldh a, [hJoyPressed]
	jr z, .ok
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
DirectionCostGlobalBaselineEnd:

DirectionCostGlobal:
	call GetJoypad
	ldh a, [hInMenu]
	and a
	ldh a, [hJoyPressed]
	jr z, .ok
	and $f0
	jr z, .held
	push bc
	ld b, a
	ldh a, [hJoyDown]
	and $0f
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
DirectionCostGlobalEnd:
