IF DEF(SAMPLED_CRY_MVP_PRISM_VBLANK)
CopyGrowlOrRoarPals::
	ld de, rSTAT
	ld a, [wFXAnimID + 1]
	if HIGH(ROAR)
		cp HIGH(ROAR)
	else
		and a
	endc
	jr nz, .growl
	ld a, [wFXAnimID]
	cp LOW(ROAR)
	jr nz, .growl
	call .roar
	ldh a, [hBGMapMode]
	and a
	jp nz, BattleAnim_TransferAnimatingPicDuringHBlank
	ret

; Growl updates the affected battler BG palette plus the shared gray OBJ palette.
.growl
	ld c, LOW(rBGPI)
	ldh a, [hBattleTurn]
	and a
	ld a, BGPI_AUTOINC | (PAL_BATTLE_BG_ENEMY * PAL_SIZE)
	jr z, .got_bg_pal
	ld a, BGPI_AUTOINC | (PAL_BATTLE_BG_PLAYER * PAL_SIZE)
.got_bg_pal
	ldh [c], a
	inc c
	ld l, a
	ld h, HIGH(wBGPals2)
	ldh a, [rLY]
	cp SCREEN_HEIGHT_PX
	jr z, .in_vblank1
.wait_no_hblank1
	ld a, [de]
	and %11
	jr z, .wait_no_hblank1
.wait_hblank1
	ld a, [de]
	and %11
	jr nz, .wait_hblank1
.in_vblank1
rept 1 palettes
	ld a, [hli]
	ldh [c], a
endr

.roar
	ld c, LOW(rOBPI)
	ld a, OBPI_AUTOINC | (PAL_BATTLE_OB_GRAY * PAL_SIZE)
	ldh [c], a
	inc c
	ld hl, wOBPals2 palette PAL_BATTLE_OB_GRAY
	ldh a, [rLY]
	cp SCREEN_HEIGHT_PX
	jr nc, .in_vblank2
.wait_no_hblank2
	ld a, [de]
	and %11
	jr z, .wait_no_hblank2
.wait_hblank2
	ld a, [de]
	and %11
	jr nz, .wait_hblank2
.in_vblank2
rept 1 palettes
	ld a, [hli]
	ldh [c], a
endr
	ret

BattleAnim_TransferAnimatingPicDuringHBlank:
	ldh a, [rWBK]
	push af
	ld a, BANK(wPokeAnimCoord)
	ldh [rWBK], a
	ld hl, wPokeAnimDestination
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ld hl, wPokeAnimCoord
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop af
	ldh [rWBK], a

	lb bc, 7, LOW(rSTAT)
.loop
	ldh a, [rLY]
	cp SCREEN_HEIGHT_PX
	jr nc, .in_vblank
.wait_no_hblank
	ldh a, [c]
	and %11
	jr z, .wait_no_hblank
.wait_hblank
	ldh a, [c]
	and %11
	jr nz, .wait_hblank
.in_vblank
rept 7
	ld a, [hli]
	ld [de], a
	inc e
endr
	ld a, [hl]
	ld [de], a

	ld a, TILEMAP_WIDTH - 7
	add e
	ld e, a
	adc d
	sub e
	ld d, a
	ld a, SCREEN_WIDTH - 7
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	dec b
	jr nz, .loop
	ret
ENDC
