; Battle animation object functions migrated to the dedicated function bank.

BattleAnimFunc_ExtNull:
	ret

BattleAnimFunc_Thunder:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	ret nz
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld e, a
	ld d, 0
	ldh a, [hBattleTurn]
	and a
	ld hl, .PlayerYCoords
	jr z, .got_y_table
	ld hl, .EnemyYCoords
.got_y_table
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], -1
	ret

.PlayerYCoords:
	db 20, 36, 52, 68

.EnemyYCoords:
	db $88 - 44, $88 - 60, $88 - 76, $88 - 92

BattleAnimFunc_ThunderStrikeController:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 51
	jr nc, .done
	inc [hl]
	ld e, a
	ld d, 0
	ld hl, .SpawnTable
	add hl, de
	add hl, de
	ld a, [hli]
	cp $ff
	ret z
	ld [wBattleObjectTempID], a
	xor a
	ld [wBattleObjectTempNamespace], a
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	ld [wBattleObjectTempXCoord], a
	xor a
	ld [wBattleObjectTempYCoord], a
	ld a, d
	ld [wBattleObjectTempParam], a
	push bc
	callfar QueueBattleAnimation
	jr c, .spawn_failed
	call BattleAnimFunc_Thunder
.spawn_failed
	pop bc
	ret

.done
	call BattleAnimExt_Deinit
	ret

.SpawnTable:
	; Frame 0: yellow 1
	db BATTLE_ANIM_OBJ_THUNDER_YELLOW_1, $0
	db BATTLE_ANIM_OBJ_THUNDER_YELLOW_1, $1
	db BATTLE_ANIM_OBJ_THUNDER_YELLOW_1, $2
	db BATTLE_ANIM_OBJ_THUNDER_YELLOW_1, $3
	db $ff, $0
	db $ff, $0
	db $ff, $0

	; Frame 7: purple
	db BATTLE_ANIM_OBJ_THUNDER_PURPLE, $0
	db BATTLE_ANIM_OBJ_THUNDER_PURPLE, $1
	db BATTLE_ANIM_OBJ_THUNDER_PURPLE, $2
	db BATTLE_ANIM_OBJ_THUNDER_PURPLE, $3
	db $ff, $0
	db $ff, $0
	db $ff, $0

	; Frame 14: yellow 2
	db BATTLE_ANIM_OBJ_THUNDER_YELLOW_2, $0
	db BATTLE_ANIM_OBJ_THUNDER_YELLOW_2, $1
	db BATTLE_ANIM_OBJ_THUNDER_YELLOW_2, $2
	db BATTLE_ANIM_OBJ_THUNDER_YELLOW_2, $3
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0

	; Frame 22: orange
	db BATTLE_ANIM_OBJ_THUNDER_ORANGE, $0
	db BATTLE_ANIM_OBJ_THUNDER_ORANGE, $1
	db BATTLE_ANIM_OBJ_THUNDER_ORANGE, $2
	db BATTLE_ANIM_OBJ_THUNDER_ORANGE, $3
	db $ff, $0
	db $ff, $0
	db $ff, $0

	; Frame 29: red
	db BATTLE_ANIM_OBJ_THUNDER_RED, $0
	db BATTLE_ANIM_OBJ_THUNDER_RED, $1
	db BATTLE_ANIM_OBJ_THUNDER_RED, $2
	db BATTLE_ANIM_OBJ_THUNDER_RED, $3
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0
	db $ff, $0

BattleAnimFunc_WaterfallBubble:
; Obj Param: bit 0 = drift right. bit 1 = faster horizontal drift.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	ld e, a
	and $1
	jr nz, .check_x
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]

.check_x
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 1, [hl]
	jr nz, .medium_x
	ld a, e
	and $3
	ret nz
	jr .move_x

.medium_x
	ld a, e
	and $1
	ret nz

.move_x
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 0, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	jr nz, .right
	dec [hl]
	ret

.right
	inc [hl]
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
	; Spawn every 6 frames to avoid stacking too many large glimmers on
	; the same scanlines.
.mod_loop
	cp 6
	jr c, .got_mod
	sub 6
	jr .mod_loop
.got_mod
	and a
	ret nz
	ld a, BATTLE_ANIM_OBJ_WISH_GLIMMER
	ld [wBattleObjectTempID], a
	xor a
	ld [wBattleObjectTempNamespace], a
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
	ld de, BATTLE_ANIM_FRAMESET_MUD_SPLASH_MEDIUM
	call ReinitBattleAnimFrameset
.splash
	ret

BattleAnimFunc_SludgeBomb:
; Slow arcing sludge projectile that turns into a three-stage splatter at impact.
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
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec a
	ld e, a
	ld d, 0
	ld hl, .ArcFrames
	add hl, de
	ld a, [hl]
	push af
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	pop af
	call BattleAnimExt_Sine
	xor $ff
	inc a
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
	call BattleAnimExt_Deinit
.splash
	ret

.ArcFrames:
	db $00, $01, $02, $03, $04, $05, $05, $06, $07, $08, $09, $0a
	db $0b, $0c, $0d, $0e, $0f, $10, $10, $11, $12, $13, $14, $15
	db $16, $17, $18, $19, $1a, $1b, $1b, $1c, $1d, $1e, $1f, $20

BattleAnimFunc_AcidBubble:
; Obj Param: $0 = center, $1 = target +24px X, $2 = target -24px X.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 40
	jr nc, .done
	ld e, a
	inc [hl]

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	ld d, a
	and a
	jr z, .center
	cp $1
	jr z, .right
	ld a, e
	cp $8
	ld a, $2
	jr c, .got_x_step
	dec a
	jr .got_x_step

.center
	ld a, e
	cp $20
	ld a, $2
	jr c, .got_x_step
	dec a
	jr .got_x_step

.right
	ld a, e
	cp $10
	ld a, $3
	jr c, .got_x_step
	dec a

.got_x_step
	ld d, a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a

	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]

	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	dec [hl]
	ld d, $10
	call BattleAnimExt_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_AcidDroplet:
; Obj Param: duration in frames.
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp d
	jr nc, .done
	inc [hl]

	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	inc [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_CrunchJaw:
; Obj Param: $0 = scripted upper jaw, $1 = scripted lower jaw.
; Enemy turn flips the rendered role.
	call BattleAnimExt_AnonJumptable
.anon_dw
	dw .init
	dw .move
	dw .delete

.init
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $1
	ld e, a
	ldh a, [hBattleTurn]
	and 1
	xor e
	ld e, a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], 12
	call BattleAnimExt_IncAnonJumptableIndex

	ld a, e
	and a
	jr z, .move_upper

	ld de, BATTLE_ANIM_FRAMESET_SHARP_TEETH_FLIPPED
	call .reinit_frameset
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], 36
	ret

.move_upper
	ld de, BATTLE_ANIM_FRAMESET_SHARP_TEETH
	call .reinit_frameset
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], -36
	ret

.move
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and a
	jr z, .delete
	dec [hl]

	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .move_upper_step

	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	sub 3
	ld [hl], a
	jr .clamp_zero

.move_upper_step
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	add 3
	ld [hl], a

.clamp_zero
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and a
	ret nz
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], 0
	ret

.delete
	call BattleAnimExt_Deinit
	ret

.reinit_frameset
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld [hl], e
	inc hl
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], 0
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], -1
	ret

BattleAnimFunc_CrunchRock:
; Obj Param: lower 3 bits select one of eight centered burst vectors.
	call BattleAnimExt_AnonJumptable
.anon_dw
	dw .init
	dw .move

.init
	call BattleAnimExt_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], 12
	ret

.move
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .done
	dec [hl]

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	add a
	ld e, a
	ld d, 0
	ld hl, .Vectors
	add hl, de

	ld a, [hli]
	ld d, a
	ld a, [hl]
	ld e, a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	bit 0, [hl]
	ret nz
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	ld e, a
	ldh a, [hBattleTurn]
	and a
	ld a, e
	jr nz, .enemy_gravity
	inc a
	jr .store_gravity

.enemy_gravity
	dec a

.store_gravity
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

.Vectors:
	db -2, -2 ; $0 upper-left
	db  2, -2 ; $1 upper-right
	db -2,  2 ; $2 lower-left
	db  2,  2 ; $3 lower-right
	db -3,  0 ; $4 left
	db  3,  0 ; $5 right
	db  0, -3 ; $6 up
	db  0,  3 ; $7 down

BattleAnimFunc_WaterPulseDriftBubble:
; Obj Param:
;   $00-$07: opening scatter bubbles, absolute screen placement.
;   $80-$87: ring-path bubbles, relative placement with short outward drift.
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .PathBubble

; Opening scatter bubble mode.
	call .GetScatterParams
	ld a, [hli]
	ld e, a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp e
	jr nc, .done

	call .GetScatterParams
	inc hl
	ld a, [hli]
	push hl
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld [hl], a
	pop hl

	ld d, [hl] ; sine amplitude
	inc hl
	ld a, [hl] ; y-move mask
	push af
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl] ; accumulated sine angle
	call BattleAnimExt_Sine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a

	pop af
	ld e, a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and e
	ret nz
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
	ret

.PathBubble:
	call .GetPathParams
	ld a, [hli]
	ld e, a ; lifetime
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp e
	jr nc, .done

	call .GetPathParams
	inc hl
	ld e, [hl] ; x velocity
	inc hl
	ld d, [hl] ; y velocity

	; Opponent-side rendering mirrors XOFFSET for RELATIVE_X objects,
	; but it does not mirror YOFFSET. Mirror only the raw Y velocity here
	; so ring-path bubble pairs spread outward instead of crossing inward.
	ldh a, [hBattleTurn]
	and a
	jr z, .got_path_velocity
	ld a, d
	xor $ff
	inc a
	ld d, a

.got_path_velocity
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a

	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

.GetScatterParams:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, .ScatterParams
	add hl, de
	ret

.GetPathParams:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, .PathParams
	add hl, de
	ret

.ScatterParams:
; lifetime, sine angle step, sine amplitude, y-move mask
	db 40, 1, 4, 1 ; $0: gentle medium
	db 35, 1, 3, 0 ; $1: tighter, faster rise
	db 20, 1, 5, 1 ; $2: short wider
	db 50, 1, 4, 1 ; $3: long gentle
	db 30, 1, 3, 0 ; $4: central fast rise
	db 40, 1, 4, 1 ; $5: spare
	db 35, 1, 3, 0 ; $6: spare
	db 20, 1, 5, 1 ; $7: spare

.PathParams:
; lifetime, x velocity, y velocity, unused
; These are small per-frame offset movements for bubbles spawned along the ring path.
	db 20,  1, -1, 0 ; $80: drift up-right
	db 20, -1,  1, 0 ; $81: drift down-left
	db 20, -1, -1, 0 ; $82: drift up-left
	db 20,  1,  1, 0 ; $83: drift down-right
	db 20,  0, -1, 0 ; $84: drift up
	db 20,  0,  1, 0 ; $85: drift down
	db 20,  1,  0, 0 ; $86: drift right
	db 20, -1,  0, 0 ; $87: drift left

BattleAnimFunc_AromatherapyFlower:
; Object curves down into a horizontal drift.
; Obj Param: Upper nybble = x speed. Lower nybble = curve height.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $48
	jr nc, .done
	and a
	jr nz, .got_frame
	ldh a, [hBattleTurn]
	and a
	jr z, .got_frame
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, $b4
	sub [hl]
	ld [hl], a
.got_frame
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld e, a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld d, a
	ld a, e
	cp $10
	jr c, .curve
	xor a
	jr .set_y
.curve
	push de
	call BattleAnimExt_Sine
	ld h, a
	pop de
	ld a, h
	sub d
.set_y
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	swap a
	ld e, a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ldh a, [hBattleTurn]
	and a
	ld a, [hl]
	jr nz, .move_left
	add e
	jr .store_x
.move_left
	sub e
.store_x
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_OverheatFlame:
; Object shoots outward in a fixed fan and disappears after $1c frames.
; Obj Param: Lower nybble selects one of nine X/Y vectors.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $1c
	jr nc, .done
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	cp $9
	jr c, .got_vector
	ld a, $8
.got_vector
	add a
	ld e, a
	ld d, 0
	ld hl, .Vectors
	add hl, de
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a
	ldh a, [hBattleTurn]
	and a
	ret z
	ld a, [hl]
	cp $28
	ret nc
	; Opponent-side flames render downward as raw Y decreases.
	; Delete before they enter the text box.
	jr .done

.done
	call BattleAnimExt_Deinit
	ret

.Vectors:
	db 2, -3
	db 3, -3
	db 3, -2
	db 4, -2
	db 4, -1
	db 5, -1
	db 5, -2
	db 6, -1
	db 6,  0

BattleAnimFunc_FireBlastModern:
; Obj Param: $00-$3f = orbit angle. $81-$85 = eruption direction.
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .eruption
	call BattleAnimExt_AnonJumptable
.anon_dw
	dw .orbit
	dw .travel

.orbit
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], $10
	call .apply_ring_frame
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	inc [hl]
	ret

.travel
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $88
	jr nc, .done
	add $4
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub $2
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $4
	jr z, .got_travel_radius
	dec [hl]
.got_travel_radius
	call .apply_ring_frame
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	inc [hl]
	ret

.eruption
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $14
	jr nc, .done
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	cp $1
	jr z, .eruption_up
	cp $2
	jr z, .eruption_left
	cp $3
	jr z, .eruption_right
	cp $4
	jr z, .eruption_down_left
	cp $5
	jr z, .eruption_down_right
	ret

.eruption_up
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
	ret

.eruption_down_left
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
.eruption_left
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	dec [hl]
	ret

.eruption_down_right
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
.eruption_right
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	inc [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

.apply_ring_frame
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
.apply_ring_offsets
	ld e, a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3f
	add e
	ld e, a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld d, [hl]
	push de
	call BattleAnimExt_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	ld a, e
	call BattleAnimExt_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleAnimFunc_EmberGen3:
; Obj Param: $00-$02 = projectile path. Bit 7 = target flare sweep.
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .flare

	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $14
	jr nc, .done
	ld e, a
	inc [hl]
	push de

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	cp $3
	jr c, .got_path
	ld a, $2
.got_path
	ld d, a
	add a
	add a
	add d
	add a
	add a
	pop de
	push de
	add e
	ld e, a
	ld d, 0
	ld hl, .ProjectileXSteps
	add hl, de
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a

	pop de
	ld d, 0
	ld hl, .ProjectileYSteps
	ldh a, [hBattleTurn]
	and a
	jr z, .got_projectile_y_steps
	ld hl, .ProjectileYStepsOpponent
.got_projectile_y_steps
	add hl, de
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	ret

.flare
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $14
	jr nc, .done
	and a
	call z, .init_flare
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld e, a
	ld d, 0
	ld hl, .FlareXOffsets
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

.init_flare
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	sub $4
	ld [hl], a
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub $18
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

.ProjectileXSteps:
	db 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3
	db 4, 3, 4, 4, 3, 4, 3, 4, 4, 3, 4, 3, 4, 4, 3, 4, 3, 4, 4, 3
	db 4, 5, 4, 4, 5, 4, 5, 4, 4, 5, 4, 5, 4, 4, 5, 4, 5, 4, 4, 5

.ProjectileYSteps:
	db -1, -2, -1, -1, -2, -1, -2, -1, -1, -2, -1, -2, -1, -1, -2, -1, -2, -1, -1, -2

.ProjectileYStepsOpponent:
	db -2, -3, -2, -3, -2, -3, -2, -3, -2, -3, -2, -3, -2, -3, -2, -3, -3, -3, -3, -3

.FlareXOffsets:
	db -24, -21, -19, -16, -14, -11, -9, -6, -4, -1
	db   1,   4,   6,   9,  11,  14, 16, 19, 21, 24

BattleAnimFunc_FlameWheelHit:
; Obj Param: $0 = right, $1 = left, $2 = up-left, $3 = up-right,
;            $4 = down-left, $5 = down-right.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $10
	jr nc, .done
	inc [hl]

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	cp $1
	jr z, .left
	cp $2
	jr z, .up_left
	cp $3
	jr z, .up_right
	cp $4
	jr z, .down_left
	cp $5
	jr z, .down_right

.right
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	inc [hl]
	ret

.up_left
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
.left
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	dec [hl]
	ret

.up_right
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
	jr .right

.down_left
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
	jr .left

.down_right
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
	jr .right

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_SacredFireHit:
; Obj Param: Fire Blast-style directions $1 = up, $4 = down-left,
;            $5 = down-right. High nibble may delay movement.
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	jr z, .move
	cp $10
	jr z, .delay10
	cp $20
	jr nz, .move
	ld d, 26
	jr .check_delay

.delay10
	ld d, 10

.check_delay
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp d
	jr nc, .move
	inc [hl]
	ret

.move
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	cp $1
	jr z, .up
	cp $4
	jr z, .down_left
	cp $5
	jr z, .down_right
	ret

.up
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
	ret

.down_left
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	dec [hl]
	ret

.down_right
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	inc [hl]
	ret

BattleAnimFunc_LavaPlumeEruption:
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
	ret

BattleAnimFunc_DragonClawFlame:
; Obj Param: $0-$2 = first slash trail, $3-$5 = second slash trail.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	ret nz
	inc [hl]

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	cp 6
	ret nc
	add a
	ld e, a
	ld d, 0

	ld hl, .PlayerCoords
	ldh a, [hBattleTurn]
	and a
	jr z, .got_coords
	ld hl, .EnemyCoords

.got_coords
	add hl, de
	ld e, [hl]
	inc hl
	ld d, [hl]

	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], d
	ret

.PlayerCoords:
	db 126, 44
	db 136, 56
	db 146, 68
	db 146, 44
	db 136, 56
	db 126, 68

.EnemyCoords:
	db  54, 76
	db  44, 88
	db  34, 100
	db  34, 76
	db  44, 88
	db  54, 100

BattleAnimFunc_PoisonBubble:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	add $03
	ld [hl], a
	ld d, $4
	call BattleAnimExt_Sine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	ld a, d
	and a
	jr nz, .got_y_speed
	ld d, $30
.got_y_speed
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a
	ret nc
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
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
	call BattleAnim_Sine_e
	ld a, e
	ret
