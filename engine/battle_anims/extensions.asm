; Battle animation object functions that live outside the main Move Animations bank.

BattleAnimFunc_ExtensionDispatch:
	ld hl, BATTLEANIMSTRUCT_FUNCTION
	add hl, bc
	ld a, [hl]
	sub FIRST_BATTLE_ANIM_EXTENSION_FUNC
	ld e, a
	ld d, 0
	ld hl, .Jumptable
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jp hl

.Jumptable:
; entries correspond to BATTLE_ANIM_FUNC_EXT_* constants
	table_width 2
	dw BattleAnimFunc_ExtNull
	dw BattleAnimFunc_WishStar
	dw BattleAnimFunc_SeismicTossLight
	dw BattleAnimFunc_MudShot
	assert_table_length NUM_BATTLE_ANIM_FUNCS - FIRST_BATTLE_ANIM_EXTENSION_FUNC

BattleAnimFunc_ExtNull:
	ret

BattleAnimExt_LoadIndigoFirePal:
	ld hl, .IndigoFirePal
	jp BattleAnimExt_LoadIndigoFireColorPair

.IndigoFirePal:
	RGB 15, 07, 31
	RGB 08, 02, 26

BattleAnimExt_CycleIndigoFireOBPal:
	ld hl, BG_EFFECT_STRUCT_JT_INDEX
	add hl, bc
	ld a, [hl]
	and a
	jr z, .init
	dec a
	jr z, .cycle
	jr .finish

.init
	inc [hl]
	ld hl, BG_EFFECT_STRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	jr nz, .got_speed
	ld a, [hl]
	swap a
	and $f
	jr nz, .got_speed
	ld a, $4
.got_speed
	ld e, a
	swap a
	or e
	ld hl, BG_EFFECT_STRUCT_BATTLE_TURN
	add hl, bc
	ld [hl], a
	ld hl, BG_EFFECT_STRUCT_PARAM
	add hl, bc
	ld [hl], $1
	ld hl, .CyclePals
	call BattleAnimExt_LoadIndigoFireColorPair
	ret

.cycle
	ld hl, BG_EFFECT_STRUCT_BATTLE_TURN
	add hl, bc
	ld a, [hl]
	and $f
	jr z, .apply_pal
	dec [hl]
	ret

.apply_pal
	ld a, [hl]
	swap a
	or [hl]
	ld [hl], a
	ld hl, BG_EFFECT_STRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld e, a
	inc a
	cp 6
	jr c, .store_step
	xor a
.store_step
	ld [hl], a
	ld a, e
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, .CyclePals
	add hl, de
	call BattleAnimExt_LoadIndigoFireColorPair
	ret

.finish
	call BattleAnimExt_RestoreBlueOBPal
	ld hl, BG_EFFECT_STRUCT_FUNCTION
	add hl, bc
	ld [hl], 0
	ret

.CyclePals:
	RGB 15, 07, 31
	RGB 08, 02, 26
	RGB 28, 08, 31
	RGB 18, 01, 24
	RGB 09, 11, 31
	RGB 03, 04, 29
	RGB 28, 08, 31
	RGB 18, 01, 24
	RGB 04, 16, 31
	RGB 00, 06, 31
	RGB 28, 08, 31
	RGB 18, 01, 24

BattleAnimExt_LoadIndigoFireColorPair:
	ldh a, [hCGB]
	and a
	ret z
	push bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE color 1
rept 4
	ld a, [hli]
	ld [de], a
	inc de
endr
	pop af
	ldh [rWBK], a
	pop bc
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

BattleAnimExt_RestoreBlueOBPal:
	ldh a, [hCGB]
	and a
	ret z
	push bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld hl, wOBPals1 palette PAL_BATTLE_OB_BLUE
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	ld bc, 1 palettes
	call CopyBytes
	pop af
	ldh [rWBK], a
	pop bc
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

BattleAnimExt_LoadThunderPal:
	ld a, e
	cp BATTLE_ANIM_THUNDER_PAL_RESTORE_BLUE
	jp z, BattleAnimExt_RestoreBlueOBPal
	and a
	jr z, .yellow
	dec a
	jr z, .purple
	ld hl, .RedPal
	jr .load

.yellow
	ld hl, .YellowPal
	jr .load

.purple
	ld hl, .PurplePal

.load
	jp BattleAnimExt_LoadBlueOBPal

.YellowPal:
	RGB 31, 31, 31
	RGB 31, 31, 07
	RGB 31, 16, 01
	RGB 00, 00, 00

.PurplePal:
	RGB 31, 31, 31
	RGB 24, 12, 31
	RGB 15, 08, 26
	RGB 31, 31, 31

.RedPal:
	RGB 31, 31, 31
	RGB 19, 00, 00
	RGB 19, 00, 00
	RGB 19, 00, 00

BattleAnimExt_LoadBlueOBPal:
	ldh a, [hCGB]
	and a
	ret z
	push bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	ld bc, 1 palettes
	call CopyBytes
	pop af
	ldh [rWBK], a
	pop bc
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

BattleAnimFunc_WishStar:
; Object moves right in a smooth half-sine arc over $28 frames.
; Obj Param: Upper nybble defines horizontal speed. Lower nybble defines arc height.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $28
	jr nc, .done
	inc [hl]
	ld e, a
	ld d, 0
	ld hl, .ArcFrames
	add hl, de
	ld a, [hl]
	push af
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld d, a
	pop af
	call BattleAnimExt_Sine
	xor $ff
	inc a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	swap a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	add [hl]
	ld [hl], a
	call BattleAnimFunc_WishStar_SpawnGlimmer
	ret

.done
	call BattleAnimExt_Deinit
	ret

.ArcFrames:
	db $00, $01, $02, $02, $03, $04, $05, $06
	db $06, $07, $08, $09, $0a, $0a, $0b, $0c
	db $0d, $0e, $0e, $0f, $10, $11, $12, $12
	db $13, $14, $15, $16, $16, $17, $18, $19
	db $1a, $1a, $1b, $1c, $1d, $1e, $1e, $1f

BattleAnimFunc_WishStar_SpawnGlimmer:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and $3
	ret nz
	ld a, BATTLE_ANIM_OBJ_WISH_GLIMMER
	ld [wBattleObjectTempID], a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	sub $8
	jr nc, .got_x
	xor a
.got_x
	ld [wBattleObjectTempXCoord], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	add [hl]
	ld [wBattleObjectTempYCoord], a
	xor a
	ld [wBattleObjectTempParam], a
	callfar QueueBattleAnimation
	ret

BattleAnimFunc_SeismicTossLight:
; Vertical light curtain for Seismic Toss.
; Obj Param: bit 7 = fall from top; bit 6 = constant velocity; lower nybble = initial speed.
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, a
	and $f
	jr nz, .got_initial_speed
	ld a, $5
.got_initial_speed
	ld e, a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .move
	bit 7, d
	jr nz, .init_down
	ld a, e
	xor $ff
	inc a
	jr .store_speed

.init_down
	ld a, e

.store_speed
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], $c

.move
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $80
	jp nc, BattleAnimExt_Deinit
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld e, a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	ld e, a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .check_bottom
	ld a, e
	cp $f0
	jp nc, BattleAnimExt_Deinit
	jr .check_accel

.check_bottom
	ld a, e
	cp $b8
	jp nc, BattleAnimExt_Deinit

.check_accel
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 6, [hl]
	ret nz
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	dec [hl]
	ret nz
	ld [hl], $c
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	inc [hl]
	ret

BattleAnimFunc_MudShot:
; Arcing mud projectile that turns into its splash at impact.
; Obj Param: arc height.
	call BattleAnimExt_AnonJumptable
.anon_dw
	dw .init
	dw .move
	dw .splash

.init
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	call BattleAnimExt_IncAnonJumptableIndex
.move
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	add $48
	ld d, a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp d
	jr nc, .impact
	add $2
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	call BattleAnimExt_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

.impact
	call BattleAnimExt_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	add [hl]
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	add [hl]
	ld [hl], a
	ld a, BATTLE_ANIM_FRAMESET_MUD_SPLASH
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], -1
.splash
	ret

BattleAnimExt_Deinit:
	ld hl, BATTLEANIMSTRUCT_INDEX
	add hl, bc
	ld [hl], $0
	ret

BattleAnimExt_AnonJumptable:
	pop de
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld l, [hl]
	ld h, $0
	add hl, hl
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jp hl

BattleAnimExt_IncAnonJumptableIndex:
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	inc [hl]
	ret

BattleAnimExt_Cosine:
	add %010000 ; cos(x) = sin(x + pi/2)
	; fallthrough
BattleAnimExt_Sine:
	ld e, a
	callfar BattleAnim_Sine_e
	ld a, e
	ret
