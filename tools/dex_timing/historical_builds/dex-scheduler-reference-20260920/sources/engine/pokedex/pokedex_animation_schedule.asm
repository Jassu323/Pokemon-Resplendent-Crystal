SECTION "Dex Animation Schedule Reader", ROMX, BANK[$a6]

Pokedex_ReadNextAnimationScheduleRun::
; This routine must execute in the same bank as the generated schedules.
	ld a, [wPokedexAnimScheduleAddress]
	ld l, a
	ld a, [wPokedexAnimScheduleAddress + 1]
	ld h, a

.read
	ld a, [hli]
	cp POKEDEX_ANIM_SCHEDULE_FINISH
	jr z, .finish
	cp POKEDEX_ANIM_SCHEDULE_LOOP
	jr z, .loop
	ld [wPokedexAnimScheduleRun], a
	jr .store_address

.loop
	ld e, [hl]
	inc hl
	ld d, [hl]
	inc hl
	ld a, l
	sub e
	ld l, a
	ld a, h
	sbc d
	ld h, a
	jr .read

.finish
	dec hl
	ld a, 1
	ld [wPokedexAnimScheduleRun], a

.store_address
	ld a, l
	ld [wPokedexAnimScheduleAddress], a
	ld a, h
	ld [wPokedexAnimScheduleAddress + 1], a
	ret
