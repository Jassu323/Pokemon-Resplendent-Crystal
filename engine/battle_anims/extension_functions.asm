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

BattleAnimFunc_CausticBubble:
; BubbleBeam-style fast launch/deceleration, then pop into one acid droplet.
	call BattleAnimExt_AnonJumptable
.anon_dw
	dw .init
	dw .launch
	dw .drift
	dw .pop

.init
	call BattleAnimExt_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], 12
	call .ApplyLaneYOffset
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub (5 * TILE_WIDTH) + 20
	ld [hl], a
	ret

.ApplyLaneYOffset:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	cp $90
	jr z, .lane_high
	cp $b0
	jr z, .lane_mid
	cp $f0
	jr z, .lane_low
	ret

.lane_high
	ld d, 0
	ldh a, [hBattleTurn]
	and a
	jr z, .got_high_offset
	ld d, 12
.got_high_offset
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub d
	ld [hl], a
	ret

.lane_mid
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add 8
	ld [hl], a
	ret

.lane_low
	ld d, 4
	ldh a, [hBattleTurn]
	and a
	jr z, .got_low_offset
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub 8
	ld [hl], a
	ret
.got_low_offset
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a
	ret

.launch
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .start_drift
	dec [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	call .StepToTarget
	ret

.StepToTarget:
	and $f
	ld e, a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	add [hl]
	ld [hl], a
	srl e
	ret z
	ldh a, [hBattleTurn]
	and a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	jr nz, .step_y_down
.step_y_up
	dec [hl]
	dec e
	jr nz, .step_y_up
	ret
.step_y_down
	inc [hl]
	dec e
	jr nz, .step_y_down
	ret

.start_drift
	call BattleAnimExt_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], 0
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], 0
	ret

.drift
	call .Decelerate
	call .ReachedPopX
	jr nc, .start_pop
	ret

.start_pop
	call BattleAnimExt_IncAnonJumptableIndex
	ld de, BATTLE_ANIM_FRAMESET_BUBBLE_BURST_POP
	call ReinitBattleAnimFrameset
	ld de, SFX_TOXIC
	ld a, $1 ; anim_sound 0, 1
	call BattleAnimController_PlayStereoSFX
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], 0
	ret

.pop
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 4
	jr nc, .done
	inc [hl]
	ret

.done
	call .SpawnDroplet
	call BattleAnimExt_Deinit
	ret

.Decelerate:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld h, [hl]
	ld l, a
	ld de, $c0
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], d

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	ld e, a
	ld d, $ff
	ldh a, [hBattleTurn]
	and a
	jr z, .got_y_delta
	xor a
	sub e
	ld e, a
	ld d, $0
.got_y_delta
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld h, [hl]
	ld l, a
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], d
	ret

.ReachedPopX:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	ld d, 132
	cp $b0
	jr nz, .not_lane1
	ld d, 144
	jr .got_threshold
.not_lane1
	cp $f0
	jr nz, .got_threshold
	ld d, 156
.got_threshold
	ldh a, [hBattleTurn]
	and a
	jr nz, .player_target_threshold
	ld a, d
	sub 8
	ld d, a
	jr .compare_pop_x
.player_target_threshold
	ld a, d
	sub 4
	ld d, a
.compare_pop_x
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp d
	ret

.SpawnDroplet:
	ld a, BATTLE_ANIM_EXT_OBJ_CAUSTIC_DROPLET
	ld [wBattleObjectTempID], a
	ld a, BATTLE_ANIM_OBJ_NAMESPACE_EXT1
	ld [wBattleObjectTempNamespace], a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	ld [wBattleObjectTempXCoord], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	ld [wBattleObjectTempYCoord], a
	ld a, $14
	ld [wBattleObjectTempParam], a
	push bc
	callfar QueueBattleAnimation
	pop bc
	ret

BattleAnimFunc_SolarBeamVerticalSegment:
	call BattleAnimExt_AnonJumptable
.anon_dw
	dw .init
	dw .done

.init
	ldh a, [hBattleTurn]
	and a
	jr z, .next
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub 5 * TILE_WIDTH
	ld [hl], a
.next
	call BattleAnimExt_IncAnonJumptableIndex
.done
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

BattleAnimFunc_AromatherapyPetal:
; Object drifts horizontally. Obj Param: upper nybble = x speed, lower two bits = starting frameset phase.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $60
	jr nc, .done
	and a
	jr nz, .got_frame
	call .SetPhaseFrameset
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
	inc [hl]
	xor a
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
	cp $a8
	jr nc, .done
	jr .store_x
.move_left
	sub e
	jr c, .done
.store_x
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

.SetPhaseFrameset
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	ret z
	add BATTLE_ANIM_FRAMESET_PINK_PETAL
	ld e, a
	ld d, 0
	jp ReinitBattleAnimFrameset

BattleAnimFunc_AuroraBeamRing:
; Object moves from user to target for 36 frames, then disappears.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 36
	jr nc, .done
	inc [hl]
	ld a, $2
	call BattleAnim_StepToTarget
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_AeroblastWave:
; Obj Param: low two bits select starting flip phase.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .move

.init
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	jr z, .move
	add BATTLE_ANIM_FRAMESET_AEROBLAST_WAVE
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
.move
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 15
	jr nc, .done
	inc [hl]
	ld a, $4
	call BattleAnim_StepToTarget
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_DiveBombWind:
; Obj Param: starting angle.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .update

.init
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a

.update
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	push af
	ld d, 12
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop af
	ld d, 24
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	add $2
	ld [hl], a
	ret

BattleAnimFunc_VoltTackleBolt:
; Obj Param: 0-4 selects horizontal bolt lane.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .wait

.init
	call BattleAnim_IncAnonJumptableIndex
	ld a, 80
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	cp 5
	jr c, .got_lane
	xor a
.got_lane
	ld e, a
	ld d, 0
	ld hl, .PlayerYCoords
	ldh a, [hBattleTurn]
	and a
	jr z, .got_y_table
	ld hl, .EnemyYCoords
.got_y_table
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and 1
	ld e, a
	ldh a, [hBattleTurn]
	and a
	jr z, .got_direction
	ld a, e
	xor 1
	ld e, a
.got_direction
	ld a, e
	and a
	ret z
	ld de, BATTLE_ANIM_FRAMESET_VOLT_TACKLE_BOLT_REVERSE
	call ReinitBattleAnimFrameset
	ret

.wait
	ret

.PlayerYCoords:
	db 92, 80, 68, 56, 44
.EnemyYCoords:
	db 44, 56, 68, 80, 92

BattleAnimFunc_BlizzardWindSheet:
; Obj Param: 0-3 selects speed and vertical phase.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 128
	jr nc, .done
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	bit 2, a
	jr z, .blizzard_speed
	and $3
	ld e, a
	ld d, 0
	ld hl, .IcyWindSpeeds
	jr .got_speed_table

.blizzard_speed
	and $3
	ld e, a
	ld d, 0
	ld hl, .Speeds
.got_speed_table
	add hl, de
	ld a, [hl]
	ld e, a
	ldh a, [hBattleTurn]
	and a
	ld a, e
	jr z, .got_x_speed
	xor $ff
	inc a
.got_x_speed
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	add [hl]
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld e, a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	add a
	add a
	add e
	and $f
	ld e, a
	ld d, 0
	ld hl, .YOffsets
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

.Speeds:
	db 7, 8, 7, 8
.IcyWindSpeeds:
	db 3, 4, 3, 4
.YOffsets:
	db  0, -1, -2, -3, -4, -5, -6, -7
	db -8, -7, -6, -5, -4, -3, -2, -1

BattleAnimFunc_PetalDancePetal:
; Obj Param: low two bits select petal animation phase, upper bits select starting angle.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw BattleAnimFunc_PetalDanceOrbit

.init
	call .SetPhaseFrameset
	jp BattleAnimFunc_PetalDanceOrbitInit

.SetPhaseFrameset
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	ret z
	add BATTLE_ANIM_FRAMESET_PINK_PETAL
	ld e, a
	ld d, 0
	jp ReinitBattleAnimFrameset

BattleAnimFunc_PetalDanceOrbitInit:
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $fc
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ldh a, [hBattleTurn]
	and a
	jr z, BattleAnimFunc_PetalDanceOrbit
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, $48 - (5 * TILE_WIDTH)
	sub [hl]
	ld [hl], a

BattleAnimFunc_PetalDanceOrbit:
; Object moves downwards in a spiral around the user.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $1
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $28
	jr nc, .end
	inc [hl]
	ret

.end
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_PetalDanceTargetPetal:
; Obj Param: low two bits select petal animation phase, upper bits select starting angle.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw BattleAnimFunc_PetalDanceTargetOrbit

.init
	call .SetPhaseFrameset
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $fc
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	jr BattleAnimFunc_PetalDanceTargetOrbit

.SetPhaseFrameset
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	ret z
	add BATTLE_ANIM_FRAMESET_PINK_PETAL
	ld e, a
	ld d, 0
	jp ReinitBattleAnimFrameset

BattleAnimFunc_PetalDanceTargetOrbit:
; Object moves upwards in a reverse spiral around the target.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld e, a
	ld a, [hl]
	xor $ff
	inc a
	add e
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	dec [hl]
	ld a, [hl]
	and $1
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $28
	jr nc, .end
	inc [hl]
	ret

.end
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

BattleAnimFunc_WillOWispBubble:
; Moves slowly toward the target with a gentle Y wobble.
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $84
	jr nc, .done
	inc a
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $1
	jr nz, .wobble
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
.wobble
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	add $2
	ld [hl], a
	ld d, $5
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_WillOWispPlusFlame:
; Obj Param: $0 = right, $1 = left, $2 = up, $3 = down.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $c
	jr nc, .done
	inc [hl]

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	cp $1
	jr z, .left
	cp $2
	jr z, .up
	cp $3
	jr z, .down

.right
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	inc [hl]
	ret

.left
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	dec [hl]
	ret

.up
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
	ret

.down
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
	ret

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

BattleAnimFunc_ShadowClawFlame:
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
	db 142, 40
	db 132, 52
	db 122, 64

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

BattleAnimFunc_ShadowBall:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 34
	jr nc, .done
	inc [hl]
	ld a, $2
	call BattleAnim_StepToTarget
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_PetalDanceController:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 40
	jr nc, .done
	ld e, a
	and $3
	jr nz, .next

	ld a, e
	srl a
	srl a
	ld e, a
	ld d, 0
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 0, [hl]
	jr nz, .target

	ld hl, .UserParams
	add hl, de
	ld d, [hl]
	ld a, BATTLE_ANIM_EXT_OBJ_PETAL_DANCE_PETAL
	call BattleAnimController_QueueExtAtController
	jr .next

.target
	ld hl, .TargetParams
	add hl, de
	ld d, [hl]
	ld a, BATTLE_ANIM_EXT_OBJ_PETAL_DANCE_TARGET_PETAL
	call BattleAnimController_QueueExtAtController

.next
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

.UserParams:
	db $00, $12, $21, $33, $40, $52, $61, $73, $80, $92
.TargetParams:
	db $00, $0a, $11, $1b, $20, $2a, $31, $3b, $00, $0a

BattleAnimFunc_ThunderboltAftereffectController:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 66
	jr nc, .done
	and a
	jr z, .frame0
	cp 6
	jr z, .flash
	cp 12
	jr z, .burst2
	cp 24
	jr z, .frame24
	cp 30
	jr z, .flash
	cp 36
	jr z, .burst2
	jr .next

.frame0
	ld de, SFX_THUNDERSHOCK_LONG
	ld a, $1 ; anim_sound 0, 1
	call BattleAnimController_PlayStereoSFX
	ld hl, .Aftereffect
	call BattleAnimController_QueueRegularFromHL
	call .QueueFlash
	ld hl, .Burst1
	call BattleAnimController_QueueRegularSet6
	jr .next

.flash
	call .QueueFlash
	jr .next

.burst2
	ld hl, .Burst2
	call BattleAnimController_QueueRegularSet6
	jr .next

.frame24
	call .QueueFlash
	ld hl, .Burst3
	call BattleAnimController_QueueRegularSet6

.next
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

.QueueFlash:
	ld d, $4
	ld e, $2
	jp BattleAnimController_QueueFlashInverted

.Aftereffect:
	db BATTLE_ANIM_OBJ_THUNDERBOLT_AFTEREFFECT, 136, 56, $0
.Burst1:
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT,       160, 56, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 148, 40, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 124, 40, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT,       112, 56, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 124, 72, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 148, 72, $0
.Burst2:
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT,       156, 44, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 136, 38, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 116, 44, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT,       116, 68, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 136, 74, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 156, 68, $0
.Burst3:
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT,       160, 64, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 144, 38, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 120, 48, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT,       112, 64, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 132, 74, $0
	db BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 152, 48, $0

BattleAnimFunc_MeteorMashController:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 104
	jr nc, .done
	and a
	jr z, .fist0
	cp 2
	jr z, .hit0
	cp 20
	jr z, .fist1
	cp 22
	jr z, .hit1
	cp 40
	jr z, .fist2
	cp 42
	jr z, .hit2
	cp 60
	jr z, .fist3
	cp 62
	jr z, .hit3
	cp 80
	jr z, .fist4
	cp 82
	jr z, .hit4
	jr .next

.fist0
	ld e, 0
	jr .fist
.fist1
	ld e, 1
	jr .fist
.fist2
	ld e, 2
	jr .fist
.fist3
	ld e, 3
	jr .fist
.fist4
	ld e, 4
.fist
	call .SpawnFist
	jr .next

.hit0
	ld e, 0
	jr .hit
.hit1
	ld e, 1
	jr .hit
.hit2
	ld e, 2
	jr .hit
.hit3
	ld e, 3
	jr .hit
.hit4
	ld e, 4
.hit
	call .SpawnHit

.next
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

.SpawnFist:
	push de
	ld de, SFX_TACKLE
	ld a, $1 ; anim_sound 0, 1
	call BattleAnimController_PlayStereoSFX
	pop de
	ld d, 0
	ld hl, .FistObjects
	add hl, de
	add hl, de
	add hl, de
	add hl, de
	jp BattleAnimController_QueueExtFromHL

.SpawnHit:
	push de
	ld d, 0
	ld hl, .HitObjects
	add hl, de
	add hl, de
	add hl, de
	add hl, de
	call BattleAnimController_QueueRegularFromHL
	pop de
	push de
	ld de, SFX_METRONOME
	ld a, $1 ; anim_sound 0, 1
	call BattleAnimController_PlayStereoSFX
	pop de
	push de
	call .SpawnStars
	pop de
	ld d, $8
	ld e, $2
	jp BattleAnimController_QueueFlashInverted

.SpawnStars:
	ld d, 0
	ld hl, .StarCoords
	add hl, de
	add hl, de
	ld d, [hl]
	inc hl
	ld e, [hl]
	ld a, BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR
	ld h, $2
	call BattleAnimController_QueueExtAtCoords
	ld a, BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR
	ld h, $3
	call BattleAnimController_QueueExtAtCoords
	ld a, BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR
	ld h, $4
	call BattleAnimController_QueueExtAtCoords
	ld a, BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR
	ld h, $5
	jp BattleAnimController_QueueExtAtCoords

.FistObjects:
	db BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 144, 36, $0
	db BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 120, 40, $0
	db BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 144, 44, $0
	db BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 120, 48, $0
	db BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 144, 52, $0
.HitObjects:
	db BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 144, 40, $0
	db BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 120, 44, $0
	db BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 144, 48, $0
	db BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 120, 52, $0
	db BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 144, 56, $0
.StarCoords:
	db 144, 40
	db 120, 44
	db 144, 48
	db 120, 52
	db 144, 56

BattleAnimController_QueueExtAtController:
; a = extended object id, d = param, bc = controller object
	ld [wBattleObjectTempID], a
	ld a, BATTLE_ANIM_OBJ_NAMESPACE_EXT1
	ld [wBattleObjectTempNamespace], a
	ld a, d
	ld [wBattleObjectTempParam], a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	ld [wBattleObjectTempXCoord], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	ld [wBattleObjectTempYCoord], a
	push bc
	callfar QueueBattleAnimation
	pop bc
	ret

BattleAnimController_QueueRegularFromHL:
	ld a, [hli]
	ld [wBattleObjectTempID], a
	xor a
	ld [wBattleObjectTempNamespace], a
	jr BattleAnimController_QueueObjectFromHL

BattleAnimController_QueueExtFromHL:
	ld a, [hli]
	ld [wBattleObjectTempID], a
	ld a, BATTLE_ANIM_OBJ_NAMESPACE_EXT1
	ld [wBattleObjectTempNamespace], a

BattleAnimController_QueueObjectFromHL:
	ld a, [hli]
	ld [wBattleObjectTempXCoord], a
	ld a, [hli]
	ld [wBattleObjectTempYCoord], a
	ld a, [hli]
	ld [wBattleObjectTempParam], a
	push hl
	push bc
	callfar QueueBattleAnimation
	pop bc
	pop hl
	ret

BattleAnimController_QueueRegularSet6:
	push bc
	ld b, 6
.loop
	call BattleAnimController_QueueRegularFromHL
	dec b
	jr nz, .loop
	pop bc
	ret

BattleAnimController_QueueExtAtCoords:
; a = extended object id, d = x, e = y, h = param
	ld [wBattleObjectTempID], a
	ld a, BATTLE_ANIM_OBJ_NAMESPACE_EXT1
	ld [wBattleObjectTempNamespace], a
	ld a, d
	ld [wBattleObjectTempXCoord], a
	ld a, e
	ld [wBattleObjectTempYCoord], a
	ld a, h
	ld [wBattleObjectTempParam], a
	push hl
	push de
	push bc
	callfar QueueBattleAnimation
	pop bc
	pop de
	pop hl
	ret

BattleAnimController_QueueFlashInverted:
; d = flash turn argument, e = flash param argument
	ld a, BATTLE_BG_EFFECT_FLASH_INVERTED
	ld [wBattleBGEffectTempID], a
	xor a
	ld [wBattleBGEffectTempJumptableIndex], a
	ld a, d
	ld [wBattleBGEffectTempTurn], a
	ld a, e
	ld [wBattleBGEffectTempParam], a
	push bc
	callfar QueueBGEffect
	pop bc
	ret

BattleAnimController_PlayStereoSFX:
; a = anim_sound duration/tracks argument, de = SFX_* id
	push hl
	push de
	push bc
	push af
	srl a
	srl a
	ld [wSFXDuration], a
	pop af
	ld c, a
	ldh a, [hBattleTurn]
	and a
	ld a, c
	jr z, .got_cry_track
	xor 1

.got_cry_track
	maskbits NUM_NOISE_CHANS
	ld [wCryTracks], a
	ld e, a
	ld d, 0
	ld hl, .Panning
	add hl, de
	ld a, [hl]
	ld [wStereoPanningMask], a
	pop bc
	pop de
	push bc
	callfar PlayStereoSFX
	pop bc
	pop hl
	ret

.Panning:
	db $f0, $0f, $f0, $0f

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
