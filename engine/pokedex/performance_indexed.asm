PokedexPerf_FastNests:
	push de
	hlcoord 0, 0
	ld bc, SCREEN_AREA
	xor a
	call ByteFill
	ld a, [wNamedObjectIndex]
	call GetPokemonIndexFromID
	dec hl
	add hl, hl
	add hl, hl
	pop de
	ld a, e
	and a
	jr z, .johto
	inc hl
	inc hl
.johto
	push af
	ld de, PokedexPerf_NestIndex
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [hli]
	ld c, a
	ld b, 0
	decoord 0, 0
	and a
	call nz, CopyBytes
	pop af
	and a
	ret nz
	farcall FindNest.RoamMon1
	farcall FindNest.RoamMon2
	ret

INCLUDE "build/dex-area-assets/tables.asm"

; Physical sample cadence is independent
; of CPU speed. Odd periods retain exact average timing rather than rounding.
SampledCry_StartBlockTimerROMX::
	xor a
	ldh [rTAC], a
	ld [wSampledCryTimerStep], a
	ld a, [wSampledCryBlockPeriod]
	ld c, a
	ldh a, [rKEY1]
	bit 7, a
	jr z, .normal
	srl c
	jr nc, .normal
	ld a, 1
	ld [wSampledCryTimerStep], a
	inc a
	ldh [hSampledCryTimer], a
	xor a
	sub c
	ldh [rTIMA], a
	dec a
	ldh [rTMA], a
	jr .start
.normal
	xor a
	sub c
	ldh [rTMA], a
	ldh [rTIMA], a
.start
	call SampledCry_ClearTimerFlag
	ldh a, [rKEY1]
	bit 7, a
	ld a, TAC_START | TAC_65KHZ
	jr z, .timer_ready
	ld a, TAC_START | TAC_16KHZ
.timer_ready
	ldh [rTAC], a
	ret
