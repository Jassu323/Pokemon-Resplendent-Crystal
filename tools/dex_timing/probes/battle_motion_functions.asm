; PRIVATE PROTOTYPE: retime local motion, never the shared update loop.
BattleMotion_WaterRing:
	ld de, MotionWaterRing
	callfar BattleMotion_ReadVar1
	jp c, BattleAnimExt_Deinit
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], d
	inc hl
	ld [hl], e
	ret

BattleMotion_WaterDrift:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	ld de, .Scatter
	bit 7, [hl]
	jr z, .lookup
	ld de, .Path
.lookup
	add a
	ld l, a
	ld h, 0
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	callfar BattleMotion_ReadVar1
	jp c, BattleAnimExt_Deinit
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr z, .write
	ldh a, [hBattleTurn]
	and a
	jr z, .write
	ld a, e
	cpl
	inc a
	ld e, a
.write
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], d
	inc hl
	ld [hl], e
	ret
.Scatter:
	dw MotionScatter0, MotionScatter1, MotionScatter2, MotionScatter3, MotionScatter4
	dw MotionScatter0, MotionScatter1, MotionScatter2
.Path:
	dw MotionPath0, MotionPath1, MotionPath2, MotionPath3
	dw MotionPath4, MotionPath5, MotionPath6, MotionPath7

BattleMotion_WaterTarget:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and 3
	add a
	ld e, a
	ld d, 0
	ld hl, .Tables
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	callfar BattleMotion_ReadVar1
	jp c, BattleAnimExt_Deinit
	; These are relative-X objects, but native motion modifies XCOORD;
	; invert the offset on the foe side to retain that native screen direction.
	ldh a, [hBattleTurn]
	and a
	jr z, .write
	ld a, d
	cpl
	inc a
	ld d, a
.write
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], d
	inc hl
	ld [hl], e
	ret
.Tables:
	dw MotionWaterTarget0, MotionWaterTarget1, MotionWaterTarget2, MotionWaterTarget3

BattleMotion_Caustic:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld e, 0
	cp $92
	jr z, .table
	ld e, 2
	cp $b3
	jr z, .table
	ld e, 4
.table
	ldh a, [hBattleTurn]
	and a
	jr z, .player
	ld a, e
	add 6
	ld e, a
.player
	ld d, 0
	ld hl, .Tables
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	callfar BattleMotion_ReadVar1
	ret c
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	add e
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], a
	and a
	ret
.Tables:
	dw MotionCausticplayer0, MotionCausticplayer1, MotionCausticplayer2
	dw MotionCausticfoe0, MotionCausticfoe1, MotionCausticfoe2

BattleMotion_SuperChip:
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .sample
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
.sample
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and 7
	cp 5
	jp nc, BattleAnimExt_Deinit
	add a
	ld e, a
	ld d, 0
	ld hl, .Tables
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	callfar BattleMotion_ReadVar1
	jp c, BattleAnimExt_Deinit
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	add e
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], a
	ret
.Tables:
	dw MotionSuperChip0, MotionSuperChip1, MotionSuperChip2, MotionSuperChip3, MotionSuperChip4

BattleMotion_DragonOrbit:
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .sample
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add 8
	ld [hl], a
.sample
	ld de, MotionDragonOrbit
	callfar BattleMotion_ReadVar2
	jp c, BattleAnimExt_Deinit
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	sub d
	ld d, e
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleMotion_ChargeDelta:
	push de
	ld de, SOLARBEAM
	call .matches
	jr z, .solar
	ld de, DAZZLING_GLEAM
	call .matches
	jr z, .dazzling
	ld de, SUPERPOWER
	call .matches
	jr z, .super
	ld hl, -$80
	jr .done
.solar
	ld hl, -$5b
	jr .done
.dazzling
	ld hl, -$5e
	jr .done
.super
	ld hl, -$45
.done
	pop de
	ret
.matches
	ld a, [wFXAnimID]
	cp e
	ret nz
	ld a, [wFXAnimID + 1]
	cp d
	ret

BattleMotion_SurfStep:
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	add 5
	cp 8
	jr c, .no_step
	sub 8
	ld [hl], a
	scf
	ret
.no_step
	ld [hl], a
	and a
	ret

; Called only when the native frameset loads a new pose. Keep all flags and
; namespaces native, and change duration only for the explicitly selected IDs.
BattleMotion_FrameDuration:
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld a, [hli]
	ld e, a
	ld a, [hl]
	and a
	ret nz
	ld a, e
	cp BATTLE_ANIM_FRAMESET_CHARGE_ORB_1
	jr z, .orb
	cp BATTLE_ANIM_FRAMESET_ABSORB_CENTER
	jr z, .center
	cp BATTLE_ANIM_FRAMESET_WATERFALL_BUBBLE
	ret nz
	ld de, WATER_PULSE
	call .matches
	ret nz
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 1, [hl]
	ld e, 60
	jr z, .set
	ld e, 48
	jr .set
.orb
	ld de, DRAGON_DANCE
	call .matches
	ld e, 18
	jr z, .set
	ld de, SOLARBEAM
	call .matches
	ld e, 23
	jr z, .set
	ld de, DAZZLING_GLEAM
	call .matches
	ld e, 22
	jr z, .set
	ld de, SUPERPOWER
	call .matches
	ld e, 30
	jr z, .set
	ret
.center
	ld de, SOLARBEAM
	call .matches
	jr z, .ordinary_center
	ld de, DAZZLING_GLEAM
	call .matches
	jr z, .ordinary_center
	ld de, SUPERPOWER
	call .matches
	ret nz
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld a, [hl]
	ld e, 62
	cp 40
	jr z, .set
	ld e, 30
	cp 20
	jr z, .set
	ld e, 5
	cp 4
	jr z, .set
	ret
.ordinary_center
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld a, [hl]
	ld e, 50
	cp 40
	jr z, .set
	ld e, 25
	cp 20
	jr z, .set
	ld e, 5
	cp 4
	jr z, .set
	ret
.set
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], e
	ret
.matches
	ld a, [wFXAnimID]
	cp e
	ret nz
	ld a, [wFXAnimID + 1]
	cp d
	ret
