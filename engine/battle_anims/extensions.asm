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
	dw BattleAnimFunc_AromatherapyFlower
	dw BattleAnimFunc_OverheatFlame
	dw BattleAnimFunc_Thunder
	dw BattleAnimFunc_WaterfallBubble
	dw BattleAnimFunc_FireBlastModern
	dw BattleAnimFunc_EmberGen3
	dw BattleAnimFunc_FlameWheelHit
	dw BattleAnimFunc_SacredFireHit
	dw BattleAnimFunc_LavaPlumeEruption
	dw BattleAnimFunc_DragonClawFlame
	assert_table_length NUM_BATTLE_ANIM_FUNCS - FIRST_BATTLE_ANIM_EXTENSION_FUNC

BattleAnimFunc_ExtNull:
	ret

BattleAnimExt_LoadFrame:
.next_frame
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	inc [hl]
	call .GetPointer
	ld a, [hli]
	cp oamrestart_command
	jr z, .restart
	cp oamend_command
	jr z, .repeat_last
	cp oamdelete_command
	jr z, .store_delete
	cp oamwait_command
	jr z, .store_wait

	ld e, a
	ld a, [hl]
	ld d, a
	and ~(OAM_YFLIP << 1 | OAM_XFLIP << 1)
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], a
	ld a, d
	and OAM_YFLIP << 1 | OAM_XFLIP << 1
	srl a
	set BATTLEANIMSTRUCT_EXT_OAMFLAGS_EXT_F, a
	jr .store_frame

.store_wait
	ld e, a
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], a
	xor a
	jr .store_frame

.store_delete
	ld e, a
	xor a
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], a

.store_frame
	ld hl, BATTLEANIMSTRUCT_EXT_OAMFLAGS
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_EXT_OAMSET
	add hl, bc
	ld [hl], e
	ret

.repeat_last
	xor a
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	dec [hl]
	dec [hl]
	jr .next_frame

.restart
	xor a
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], a
	dec a
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], a
	jr .next_frame

.GetPointer:
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld a, [hl]
	sub FIRST_BATTLE_ANIM_EXT_FRAMESET
	ld e, a
	ld d, 0
	ld hl, BattleAnimExtFrameData
	add hl, de
	add hl, de
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld l, [hl]
	ld h, 0
	add hl, hl
	add hl, de
	ret

BattleAnimExtFrameData:
; entries correspond to BATTLE_ANIM_FRAMESET_* constants starting at FIRST_BATTLE_ANIM_EXT_FRAMESET
	table_width 2
	dw .Frameset_ThunderYellow1_0 ; BATTLE_ANIM_FRAMESET_THUNDER_YELLOW_1_0
	dw .Frameset_ThunderYellow1_1 ; BATTLE_ANIM_FRAMESET_THUNDER_YELLOW_1_1
	dw .Frameset_ThunderYellow1_2 ; BATTLE_ANIM_FRAMESET_THUNDER_YELLOW_1_2
	dw .Frameset_ThunderYellow1_3 ; BATTLE_ANIM_FRAMESET_THUNDER_YELLOW_1_3
	dw .Frameset_ThunderPurple_0  ; BATTLE_ANIM_FRAMESET_THUNDER_PURPLE_0
	dw .Frameset_ThunderPurple_1  ; BATTLE_ANIM_FRAMESET_THUNDER_PURPLE_1
	dw .Frameset_ThunderPurple_2  ; BATTLE_ANIM_FRAMESET_THUNDER_PURPLE_2
	dw .Frameset_ThunderPurple_3  ; BATTLE_ANIM_FRAMESET_THUNDER_PURPLE_3
	dw .Frameset_ThunderYellow2_0 ; BATTLE_ANIM_FRAMESET_THUNDER_YELLOW_2_0
	dw .Frameset_ThunderYellow2_1 ; BATTLE_ANIM_FRAMESET_THUNDER_YELLOW_2_1
	dw .Frameset_ThunderYellow2_2 ; BATTLE_ANIM_FRAMESET_THUNDER_YELLOW_2_2
	dw .Frameset_ThunderYellow2_3 ; BATTLE_ANIM_FRAMESET_THUNDER_YELLOW_2_3
	dw .Frameset_ThunderOrange_0  ; BATTLE_ANIM_FRAMESET_THUNDER_ORANGE_0
	dw .Frameset_ThunderOrange_1  ; BATTLE_ANIM_FRAMESET_THUNDER_ORANGE_1
	dw .Frameset_ThunderOrange_2  ; BATTLE_ANIM_FRAMESET_THUNDER_ORANGE_2
	dw .Frameset_ThunderOrange_3  ; BATTLE_ANIM_FRAMESET_THUNDER_ORANGE_3
	dw .Frameset_ThunderRed_0     ; BATTLE_ANIM_FRAMESET_THUNDER_RED_0
	dw .Frameset_ThunderRed_1     ; BATTLE_ANIM_FRAMESET_THUNDER_RED_1
	dw .Frameset_ThunderRed_2     ; BATTLE_ANIM_FRAMESET_THUNDER_RED_2
	dw .Frameset_ThunderRed_3     ; BATTLE_ANIM_FRAMESET_THUNDER_RED_3
	dw .Frameset_ThunderboltStrike ; BATTLE_ANIM_FRAMESET_THUNDERBOLT_STRIKE
	dw .Frameset_ThunderboltAftereffect ; BATTLE_ANIM_FRAMESET_THUNDERBOLT_AFTEREFFECT
	dw .Frameset_HydroPumpColumn ; BATTLE_ANIM_FRAMESET_HYDRO_PUMP_COLUMN
	dw .Frameset_HydroPumpColumnSlow ; BATTLE_ANIM_FRAMESET_HYDRO_PUMP_COLUMN_SLOW
	dw .Frameset_VineWhip ; BATTLE_ANIM_FRAMESET_VINE_WHIP
	dw .Frameset_DragonClawSlash ; BATTLE_ANIM_FRAMESET_DRAGON_CLAW_SLASH
	dw .Frameset_DragonClawSlashXFlip ; BATTLE_ANIM_FRAMESET_DRAGON_CLAW_SLASH_XFLIP
	assert_table_length NUM_BATTLE_ANIM_EXT_FRAMESETS

.Frameset_ThunderYellow1_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_0, 5
	oamdelete

.Frameset_ThunderYellow1_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_1, 5
	oamdelete

.Frameset_ThunderYellow1_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_2, 5
	oamdelete

.Frameset_ThunderYellow1_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_3, 5
	oamdelete

.Frameset_ThunderPurple_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_0, 5
	oamdelete

.Frameset_ThunderPurple_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_1, 5
	oamdelete

.Frameset_ThunderPurple_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_2, 5
	oamdelete

.Frameset_ThunderPurple_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_3, 5
	oamdelete

.Frameset_ThunderYellow2_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_0, 5
	oamdelete

.Frameset_ThunderYellow2_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_1, 5
	oamdelete

.Frameset_ThunderYellow2_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_2, 5
	oamdelete

.Frameset_ThunderYellow2_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_3, 5
	oamdelete

.Frameset_ThunderOrange_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_0, 5
	oamdelete

.Frameset_ThunderOrange_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_1, 5
	oamdelete

.Frameset_ThunderOrange_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_2, 5
	oamdelete

.Frameset_ThunderOrange_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_3, 5
	oamdelete

.Frameset_ThunderRed_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_0, 5
	oamdelete

.Frameset_ThunderRed_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_1, 5
	oamdelete

.Frameset_ThunderRed_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_2, 5
	oamdelete

.Frameset_ThunderRed_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_3, 5
	oamdelete

.Frameset_ThunderboltStrike:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_1, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_2, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_3, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_4, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_5, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_6, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_7, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_8, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_9, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_10, 9
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_9, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_8, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_7, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_6, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_5, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_4, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_3, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_2, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_1, 1
	oamdelete

.Frameset_ThunderboltAftereffect:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_SMALL, 3
	oamwait 3
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_MEDIUM, 3
	oamwait 3
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_LARGE, 6
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_SMALL, 3
	oamwait 3
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_MEDIUM, 3
	oamwait 3
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_LARGE, 6
	oamwait 3
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_SMALL, 3
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_MEDIUM, 3
	oamdelete

.Frameset_HydroPumpColumn:
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_5ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_5ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1ROW, 1
	oamdelete

.Frameset_HydroPumpColumnSlow:
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_5ROW, 1
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1_6ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_5ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2ROW, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1ROW, 2
	oamdelete

.Frameset_VineWhip:
	oamframe BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_1, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_2, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_3, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_4, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_5, 4
	oamdelete

.Frameset_DragonClawSlash:
	oamwait 10
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_1, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_2, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_3, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_4, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_5, 4
	oamdelete

.Frameset_DragonClawSlashXFlip:
	oamwait 55
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_1, 4, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_2, 4, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_3, 4, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_4, 4, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_5, 4, B_OAM_XFLIP
	oamdelete

BattleAnimExtOAMUpdate:
	ld l, e
	ld h, 0
	ld de, BattleAnimExtOAMData
	add hl, hl
	add hl, hl
	add hl, de
	ld a, [wBattleAnimTempTileID]
	add [hl] ; tile offset
	ld [wBattleAnimTempTileID], a
	inc hl
	ld a, [hli] ; oam data length
	ld c, a
	ld a, [hli] ; oam data pointer
	ld h, [hl]
	ld l, a
	ld a, [wBattleAnimOAMPointerLo]
	ld e, a
	ld d, HIGH(wShadowOAM)

.loop
	; Y Coord
	ld a, [wBattleAnimTempYCoord]
	ld b, a
	ld a, [wBattleAnimTempYOffset]
	add b
	ld b, a
	push hl
	ld a, [hl]
	ld hl, wBattleAnimTempOAMFlags
	bit B_OAM_YFLIP, [hl]
	jr z, .no_yflip
	add $8
	xor $ff
	inc a
.no_yflip
	pop hl
	add b
	ld [de], a

	; X Coord
	inc hl
	inc de
	ld a, [wBattleAnimTempXCoord]
	ld b, a
	ld a, [wBattleAnimTempXOffset]
	add b
	ld b, a
	push hl
	ld a, [hl]
	ld hl, wBattleAnimTempOAMFlags
	bit B_OAM_XFLIP, [hl]
	jr z, .no_xflip
	add $8
	xor $ff
	inc a
.no_xflip
	pop hl
	add b
	ld [de], a

	; Tile ID
	inc hl
	inc de
	ld a, [wBattleAnimTempTileID]
	add BATTLEANIM_BASE_TILE
	add [hl]
	ld [de], a

	; Attributes
	inc hl
	inc de
	ld a, [wBattleAnimTempOAMFlags]
	ld b, a
	ld a, [hl]
	xor b
	and OAM_PRIO | OAM_YFLIP | OAM_XFLIP
	ld b, a
	ld a, [hl]
	and OAM_PAL1
	or b
	ld b, a
	ld a, [wBattleAnimTempPalette]
	and OAM_PALETTE | OAM_BANK1
	or b
	ld [de], a

	inc hl
	inc de
	ld a, e
	ld [wBattleAnimOAMPointerLo], a
	cp LOW(wShadowOAMEnd)
	jr nc, .exit_set_carry
	dec c
	jr nz, .loop
	and a
	ret

.exit_set_carry
	scf
	ret

BattleAnimExtOAMData:
; entries correspond to BATTLE_ANIM_EXT_OAMSET_* constants
	table_width 4
	battleanimoam $00, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_0
	battleanimoam $04, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_1
	battleanimoam $08, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_2
	battleanimoam $04, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_3
	battleanimoam $10, 8, .OAMData_ThunderWideSection   ; BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_0
	battleanimoam $14, 8, .OAMData_ThunderWideSection   ; BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_1
	battleanimoam $18, 8, .OAMData_ThunderWideSection   ; BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_2
	battleanimoam $14, 8, .OAMData_ThunderWideSection   ; BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_3
	battleanimoam $20, 8, .OAMData_ThunderWideSection   ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_0
	battleanimoam $24, 8, .OAMData_ThunderWideSection   ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_1
	battleanimoam $28, 8, .OAMData_ThunderWideSection   ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_2
	battleanimoam $24, 8, .OAMData_ThunderWideSection   ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_3
	battleanimoam $30, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_0
	battleanimoam $34, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_1
	battleanimoam $38, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_2
	battleanimoam $34, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_3
	battleanimoam $40, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_0
	battleanimoam $44, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_1
	battleanimoam $48, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_2
	battleanimoam $44, 4, .OAMData_ThunderNarrowSection ; BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_3
	battleanimoam $00,  2, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_1
	battleanimoam $00,  4, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_2
	battleanimoam $00,  6, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_3
	battleanimoam $00,  8, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_4
	battleanimoam $00, 10, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_5
	battleanimoam $00, 12, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_6
	battleanimoam $00, 14, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_7
	battleanimoam $00, 16, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_8
	battleanimoam $00, 18, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_9
	battleanimoam $00, 20, .OAMData_ThunderboltStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_10
	battleanimoam $00, 18, .OAMData_ThunderboltStrike + 2 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_9
	battleanimoam $00, 16, .OAMData_ThunderboltStrike + 4 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_8
	battleanimoam $00, 14, .OAMData_ThunderboltStrike + 6 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_7
	battleanimoam $00, 12, .OAMData_ThunderboltStrike + 8 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_6
	battleanimoam $00, 10, .OAMData_ThunderboltStrike + 10 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_5
	battleanimoam $00,  8, .OAMData_ThunderboltStrike + 12 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_4
	battleanimoam $00,  6, .OAMData_ThunderboltStrike + 14 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_3
	battleanimoam $00,  4, .OAMData_ThunderboltStrike + 16 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_2
	battleanimoam $00,  2, .OAMData_ThunderboltStrike + 18 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_STRIKE_LOWER_1
	battleanimoam $00, 10, .OAMData_ThunderboltAftereffectSmall ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_SMALL
	battleanimoam $00, 12, .OAMData_ThunderboltAftereffectMedium ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_MEDIUM
	battleanimoam $00, 16, .OAMData_ThunderboltAftereffectLarge ; BATTLE_ANIM_EXT_OAMSET_THUNDERBOLT_AFTEREFFECT_LARGE
	battleanimoam $00,  2, .OAMData_WaterColumn1Row ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1ROW
	battleanimoam $00,  4, .OAMData_WaterColumn2Row ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2ROW
	battleanimoam $00,  6, .OAMData_WaterColumn3Row ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3ROW
	battleanimoam $00,  8, .OAMData_WaterColumn4Row ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4ROW
	battleanimoam $00, 10, .OAMData_WaterColumn5Row ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_5ROW
	battleanimoam $00, 12, .OAMData_WaterColumn ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_1_6ROW
	battleanimoam $0c, 12, .OAMData_WaterColumn ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_2_6ROW
	battleanimoam $18, 12, .OAMData_WaterColumn ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_3_6ROW
	battleanimoam $24, 12, .OAMData_WaterColumn ; BATTLE_ANIM_EXT_OAMSET_WATER_COLUMN_4_6ROW
	battleanimoam $00,  8, .OAMData_VineWhip1 ; BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_1
	battleanimoam $00,  9, .OAMData_VineWhip2 ; BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_2
	battleanimoam $00,  8, .OAMData_VineWhip3 ; BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_3
	battleanimoam $00,  7, .OAMData_VineWhip4 ; BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_4
	battleanimoam $00,  8, .OAMData_VineWhip5 ; BATTLE_ANIM_EXT_OAMSET_VINE_WHIP_5
	battleanimoam $00,  1, .OAMData_DragonClawSlash1 ; BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_1
	battleanimoam $01,  4, .OAMData_DragonClawSlash2 ; BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_2
	battleanimoam $05,  8, .OAMData_DragonClawSlash3 ; BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_3
	battleanimoam $0d, 10, .OAMData_DragonClawSlash4 ; BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_4
	battleanimoam $17, 10, .OAMData_DragonClawSlash5 ; BATTLE_ANIM_EXT_OAMSET_DRAGON_CLAW_SLASH_5
	assert_table_length NUM_BATTLE_ANIM_EXT_OAMSETS

.OAMData_ThunderNarrowSection:
	dbsprite  -1, 0, 0, 0, $01, $0
	dbsprite   0, 0, 0, 0, $02, $0
	dbsprite  -1, 1, 0, 0, $05, $0
	dbsprite   0, 1, 0, 0, $06, $0

.OAMData_ThunderWideSection:
	dbsprite  -2, 0, 0, 0, $00, $0
	dbsprite  -1, 0, 0, 0, $01, $0
	dbsprite   0, 0, 0, 0, $02, $0
	dbsprite   1, 0, 0, 0, $03, $0
	dbsprite  -2, 1, 0, 0, $04, $0
	dbsprite  -1, 1, 0, 0, $05, $0
	dbsprite   0, 1, 0, 0, $06, $0
	dbsprite   1, 1, 0, 0, $07, $0

.OAMData_ThunderboltStrike:
	dbsprite  -1, -7, 0, 0, $00, $0
	dbsprite   0, -7, 0, 0, $01, $0
	dbsprite  -1, -6, 0, 0, $02, $0
	dbsprite   0, -6, 0, 0, $03, $0
	dbsprite  -1, -5, 0, 0, $04, $0
	dbsprite   0, -5, 0, 0, $05, $0
	dbsprite  -1, -4, 0, 0, $06, $0
	dbsprite   0, -4, 0, 0, $07, $0
	dbsprite  -1, -3, 0, 0, $08, $0
	dbsprite   0, -3, 0, 0, $09, $0
	dbsprite  -1, -2, 0, 0, $0a, $0
	dbsprite   0, -2, 0, 0, $0b, $0
	dbsprite  -1, -1, 0, 0, $0c, $0
	dbsprite   0, -1, 0, 0, $0d, $0
	dbsprite  -1,  0, 0, 0, $0e, $0
	dbsprite   0,  0, 0, 0, $0f, $0
	dbsprite  -1,  1, 0, 0, $00, $0
	dbsprite   0,  1, 0, 0, $01, $0
	dbsprite  -1,  2, 0, 0, $02, $0
	dbsprite   0,  2, 0, 0, $03, $0

.OAMData_ThunderboltAftereffectSmall:
	dbsprite  -2, -1, 0, 0, $00, $0
	dbsprite  -1, -1, 0, 0, $01, $0
	dbsprite   0, -1, 0, 0, $02, $0
	dbsprite   1, -1, 0, 0, $03, $0
	dbsprite  -2,  0, 0, 0, $04, $0
	dbsprite  -1,  0, 0, 0, $05, $0
	dbsprite   0,  0, 0, 0, $06, $0
	dbsprite   1,  0, 0, 0, $07, $0
	dbsprite  -1,  1, 0, 0, $09, $0
	dbsprite   0,  1, 0, 0, $0a, $0

.OAMData_ThunderboltAftereffectMedium:
	dbsprite  -2, -1, 0, 0, $0c, $0
	dbsprite  -1, -1, 0, 0, $0d, $0
	dbsprite   0, -1, 0, 0, $0e, $0
	dbsprite   1, -1, 0, 0, $0f, $0
	dbsprite  -2,  0, 0, 0, $10, $0
	dbsprite  -1,  0, 0, 0, $11, $0
	dbsprite   0,  0, 0, 0, $12, $0
	dbsprite   1,  0, 0, 0, $13, $0
	dbsprite  -2,  1, 0, 0, $14, $0
	dbsprite  -1,  1, 0, 0, $15, $0
	dbsprite   0,  1, 0, 0, $16, $0
	dbsprite   1,  1, 0, 0, $17, $0

.OAMData_ThunderboltAftereffectLarge:
	dbsprite  -2, -2, 0, 4, $18, $0
	dbsprite  -1, -2, 0, 4, $19, $0
	dbsprite   0, -2, 0, 4, $1a, $0
	dbsprite   1, -2, 0, 4, $1b, $0
	dbsprite  -2, -1, 0, 4, $1c, $0
	dbsprite  -1, -1, 0, 4, $1d, $0
	dbsprite   0, -1, 0, 4, $1e, $0
	dbsprite   1, -1, 0, 4, $1f, $0
	dbsprite  -2,  0, 0, 4, $20, $0
	dbsprite  -1,  0, 0, 4, $21, $0
	dbsprite   0,  0, 0, 4, $22, $0
	dbsprite   1,  0, 0, 4, $23, $0
	dbsprite  -2,  1, 0, 4, $24, $0
	dbsprite  -1,  1, 0, 4, $25, $0
	dbsprite   0,  1, 0, 4, $26, $0
	dbsprite   1,  1, 0, 4, $27, $0

.OAMData_WaterColumn:
	dbsprite  -1, -6, 0, 0, $00, $0
	dbsprite   0, -6, 0, 0, $01, $0
	dbsprite  -1, -5, 0, 0, $02, $0
	dbsprite   0, -5, 0, 0, $03, $0
	dbsprite  -1, -4, 0, 0, $04, $0
	dbsprite   0, -4, 0, 0, $05, $0
	dbsprite  -1, -3, 0, 0, $06, $0
	dbsprite   0, -3, 0, 0, $07, $0
	dbsprite  -1, -2, 0, 0, $08, $0
	dbsprite   0, -2, 0, 0, $09, $0
	dbsprite  -1, -1, 0, 0, $0a, $0
	dbsprite   0, -1, 0, 0, $0b, $0

.OAMData_WaterColumn1Row:
	dbsprite  -1, -1, 0, 0, $00, $0
	dbsprite   0, -1, 0, 0, $01, $0

.OAMData_WaterColumn2Row:
	dbsprite  -1, -2, 0, 0, $00, $0
	dbsprite   0, -2, 0, 0, $01, $0
	dbsprite  -1, -1, 0, 0, $02, $0
	dbsprite   0, -1, 0, 0, $03, $0

.OAMData_WaterColumn3Row:
	dbsprite  -1, -3, 0, 0, $00, $0
	dbsprite   0, -3, 0, 0, $01, $0
	dbsprite  -1, -2, 0, 0, $02, $0
	dbsprite   0, -2, 0, 0, $03, $0
	dbsprite  -1, -1, 0, 0, $04, $0
	dbsprite   0, -1, 0, 0, $05, $0

.OAMData_WaterColumn4Row:
	dbsprite  -1, -4, 0, 0, $00, $0
	dbsprite   0, -4, 0, 0, $01, $0
	dbsprite  -1, -3, 0, 0, $02, $0
	dbsprite   0, -3, 0, 0, $03, $0
	dbsprite  -1, -2, 0, 0, $04, $0
	dbsprite   0, -2, 0, 0, $05, $0
	dbsprite  -1, -1, 0, 0, $06, $0
	dbsprite   0, -1, 0, 0, $07, $0

.OAMData_WaterColumn5Row:
	dbsprite  -1, -5, 0, 0, $00, $0
	dbsprite   0, -5, 0, 0, $01, $0
	dbsprite  -1, -4, 0, 0, $02, $0
	dbsprite   0, -4, 0, 0, $03, $0
	dbsprite  -1, -3, 0, 0, $04, $0
	dbsprite   0, -3, 0, 0, $05, $0
	dbsprite  -1, -2, 0, 0, $06, $0
	dbsprite   0, -2, 0, 0, $07, $0
	dbsprite  -1, -1, 0, 0, $08, $0
	dbsprite   0, -1, 0, 0, $09, $0

.OAMData_VineWhip1:
	dbsprite  -2, -1, 0, 0, $00, $0
	dbsprite  -1, -1, 0, 0, $01, $0
	dbsprite   0, -1, 0, 0, $02, $0
	dbsprite  -2,  0, 0, 0, $03, $0
	dbsprite   0,  0, 0, 0, $04, $0
	dbsprite  -2,  1, 0, 0, $05, $0
	dbsprite  -1,  1, 0, 0, $06, $0
	dbsprite   0,  1, 0, 0, $07, $0

.OAMData_VineWhip2:
	dbsprite  -1, -2, 0, 0, $08, $0
	dbsprite   0, -2, 0, 0, $09, $0
	dbsprite   1, -2, 0, 0, $0a, $0
	dbsprite   1, -1, 0, 0, $0b, $0
	dbsprite   1,  0, 0, 0, $0c, $0
	dbsprite  -2,  1, 0, 0, $0d, $0
	dbsprite  -1,  1, 0, 0, $0e, $0
	dbsprite   0,  1, 0, 0, $0f, $0
	dbsprite   1,  1, 0, 0, $10, $0

.OAMData_VineWhip3:
	dbsprite  -2, -1, 0, 0, $11, $0
	dbsprite  -1, -1, 0, 0, $12, $0
	dbsprite  -2,  0, 0, 0, $13, $0
	dbsprite  -1,  0, 0, 0, $14, $0
	dbsprite   0,  0, 0, 0, $15, $0
	dbsprite  -2,  1, 0, 0, $16, $0
	dbsprite   0,  1, 0, 0, $17, $0
	dbsprite   1,  1, 0, 0, $18, $0

.OAMData_VineWhip4:
	dbsprite  -2, -1, 0, 0, $19, $0
	dbsprite  -1, -1, 0, 0, $1a, $0
	dbsprite   0, -1, 0, 0, $1b, $0
	dbsprite   1, -1, 0, 0, $1c, $0
	dbsprite  -2,  0, 0, 0, $1d, $0
	dbsprite   1,  0, 0, 0, $1e, $0
	dbsprite  -2,  1, 0, 0, $1f, $0

.OAMData_VineWhip5:
	dbsprite  -2, -2, 0, 0, $20, $0
	dbsprite  -1, -2, 0, 0, $21, $0
	dbsprite   0, -2, 0, 0, $22, $0
	dbsprite  -2, -1, 0, 0, $23, $0
	dbsprite   0, -1, 0, 0, $24, $0
	dbsprite   1, -1, 0, 0, $25, $0
	dbsprite  -2,  0, 0, 0, $26, $0
	dbsprite  -2,  1, 0, 0, $27, $0

.OAMData_DragonClawSlash1:
	dbsprite  -2, -2, 0, 0, $00, $0

.OAMData_DragonClawSlash2:
	dbsprite  -2, -2, 0, 0, $00, $0
	dbsprite  -1, -2, 0, 0, $01, $0
	dbsprite  -2, -1, 0, 0, $02, $0
	dbsprite  -1, -1, 0, 0, $03, $0

.OAMData_DragonClawSlash3:
	dbsprite  -2, -2, 0, 0, $00, $0
	dbsprite  -1, -2, 0, 0, $01, $0
	dbsprite  -2, -1, 0, 0, $02, $0
	dbsprite  -1, -1, 0, 0, $03, $0
	dbsprite   0, -1, 0, 0, $04, $0
	dbsprite  -1,  0, 0, 0, $05, $0
	dbsprite   0,  0, 0, 0, $06, $0
	dbsprite   1,  1, 0, 0, $07, $0

.OAMData_DragonClawSlash4:
	dbsprite  -2, -2, 0, 0, $00, $0
	dbsprite  -1, -2, 0, 0, $01, $0
	dbsprite  -2, -1, 0, 0, $02, $0
	dbsprite  -1, -1, 0, 0, $03, $0
	dbsprite   0, -1, 0, 0, $04, $0
	dbsprite  -1,  0, 0, 0, $05, $0
	dbsprite   0,  0, 0, 0, $06, $0
	dbsprite   1,  0, 0, 0, $07, $0
	dbsprite   0,  1, 0, 0, $08, $0
	dbsprite   1,  1, 0, 0, $09, $0

.OAMData_DragonClawSlash5:
	dbsprite  -2, -2, 0, 0, $00, $0
	dbsprite  -1, -2, 0, 0, $01, $0
	dbsprite  -2, -1, 0, 0, $02, $0
	dbsprite  -1, -1, 0, 0, $03, $0
	dbsprite   0, -1, 0, 0, $04, $0
	dbsprite  -1,  0, 0, 0, $05, $0
	dbsprite   0,  0, 0, 0, $06, $0
	dbsprite   1,  0, 0, 0, $07, $0
	dbsprite   0,  1, 0, 0, $08, $0
	dbsprite   1,  1, 0, 0, $09, $0

BattleAnimExt_LoadIndigoFirePal:
	ld hl, .IndigoFirePal
	jp BattleAnimExt_LoadIndigoFireColors

.IndigoFirePal:
	RGB 04, 01, 16
	RGB 08, 02, 26
	RGB 15, 07, 31

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
	call BattleAnimExt_LoadIndigoFireColors
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
	add e
	add a
	ld e, a
	ld d, 0
	ld hl, .CyclePals
	add hl, de
	call BattleAnimExt_LoadIndigoFireColors
	ret

.finish
	call BattleAnimExt_RestoreBlueOBPal
	ld hl, BG_EFFECT_STRUCT_FUNCTION
	add hl, bc
	ld [hl], 0
	ret

.CyclePals:
	RGB 04, 01, 16
	RGB 08, 02, 26
	RGB 15, 07, 31
	RGB 08, 00, 14
	RGB 18, 01, 24
	RGB 28, 08, 31
	RGB 01, 02, 16
	RGB 03, 04, 29
	RGB 09, 11, 31
	RGB 08, 00, 14
	RGB 18, 01, 24
	RGB 28, 08, 31
	RGB 00, 03, 16
	RGB 00, 06, 31
	RGB 04, 16, 31
	RGB 08, 00, 14
	RGB 18, 01, 24
	RGB 28, 08, 31

BattleAnimExt_LoadIndigoFireColors:
	ldh a, [hCGB]
	and a
	ret z
	push bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE color 1
rept 6
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
	cp BATTLE_ANIM_THUNDER_PAL_RESTORE
	jr z, .restore
	ldh a, [hCGB]
	and a
	ret z
	push bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld hl, .PurplePal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	ld bc, 1 palettes
	call CopyBytes
	ld hl, .OrangePal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BROWN
	ld bc, 1 palettes
	call CopyBytes
	ld hl, .RedPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_RED
	ld bc, 1 palettes
	call CopyBytes
	jr .done

.restore
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
	ld hl, wOBPals1 palette PAL_BATTLE_OB_BROWN
	ld de, wOBPals2 palette PAL_BATTLE_OB_BROWN
	ld bc, 1 palettes
	call CopyBytes
	ld hl, wOBPals1 palette PAL_BATTLE_OB_RED
	ld de, wOBPals2 palette PAL_BATTLE_OB_RED
	ld bc, 1 palettes
	call CopyBytes

.done
	pop af
	ldh [rWBK], a
	pop bc
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

.PurplePal:
	RGB 31, 31, 31
	RGB 24, 12, 31
	RGB 15, 08, 26
	RGB 31, 31, 31

.OrangePal:
	RGB 31, 31, 31
	RGB 31, 24, 07
	RGB 31, 16, 01
	RGB 00, 00, 00

.RedPal:
	RGB 31, 31, 31
	RGB 19, 00, 00
	RGB 19, 00, 00
	RGB 19, 00, 00

BattleAnimExt_LoadThunderboltPal:
	ld a, e
	cp BATTLE_ANIM_WATER_COLUMN_PAL_LOAD
	jr z, .load_water_column
	cp BATTLE_ANIM_GRASS_PAL_LOAD
	jr z, .load_grass
	cp BATTLE_ANIM_FIRE_PAL_LOAD
	jr z, .load_fire
	cp BATTLE_ANIM_DRAGON_PAL_LOAD
	jr z, .load_dragon
	cp BATTLE_ANIM_FIRE_BLUE_PAL_LOAD
	jr z, .load_fire_blue
	cp BATTLE_ANIM_DRAGON_CLAW_PAL_LOAD
	jr z, .load_dragon_claw
	cp BATTLE_ANIM_DRAGON_BLUE_PAL_LOAD
	jr z, .load_dragon_blue
	cp BATTLE_ANIM_WATER_COLUMN_PAL_RESTORE
	jr z, .restore_blue
	cp BATTLE_ANIM_GRASS_PAL_RESTORE
	jr z, .restore_green
	cp BATTLE_ANIM_FIRE_PAL_RESTORE
	jr z, .restore_red
	cp BATTLE_ANIM_DRAGON_PAL_RESTORE
	jr z, .restore_red
	cp BATTLE_ANIM_FIRE_BLUE_PAL_RESTORE
	jr z, .restore_blue
	cp BATTLE_ANIM_DRAGON_CLAW_PAL_RESTORE
	jr z, .restore_red
	cp BATTLE_ANIM_DRAGON_BLUE_PAL_RESTORE
	jr z, .restore_blue
	cp BATTLE_ANIM_THUNDERBOLT_PAL_RESTORE
	jr z, .restore_blue
	ld hl, .ThunderboltPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_water_column
	ld hl, .WaterColumnPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_grass
	ld hl, .GrassPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_GREEN
	jr .load_custom_pal

.load_fire
	ld hl, .FirePal
	ld de, wOBPals2 palette PAL_BATTLE_OB_RED
	jr .load_custom_pal

.load_dragon
	ld hl, .DragonPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_RED
	jr .load_custom_pal

.load_dragon_blue
	ld hl, .DragonPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_fire_blue
	ld hl, .FireBluePal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_dragon_claw
	ld hl, .DragonClawPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_RED

.load_custom_pal
	ldh a, [hCGB]
	and a
	ret z
	push bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld bc, 1 palettes
	call CopyBytes
	jr .done

.restore_blue
	ld hl, wOBPals1 palette PAL_BATTLE_OB_BLUE
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .restore_pal

.restore_green
	ld hl, wOBPals1 palette PAL_BATTLE_OB_GREEN
	ld de, wOBPals2 palette PAL_BATTLE_OB_GREEN
	jr .restore_pal

.restore_red
	ld hl, wOBPals1 palette PAL_BATTLE_OB_RED
	ld de, wOBPals2 palette PAL_BATTLE_OB_RED

.restore_pal
	ldh a, [hCGB]
	and a
	ret z
	push bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld bc, 1 palettes
	call CopyBytes

.done
	pop af
	ldh [rWBK], a
	pop bc
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

.ThunderboltPal:
	RGB 31, 31, 31
	RGB 07, 06, 31
	RGB 31, 31, 07
	RGB 07, 30, 23

.WaterColumnPal:
	RGB 31, 31, 31
	RGB 01, 07, 31
	RGB 01, 20, 31
	RGB 12, 29, 31

.GrassPal:
	RGB 31, 31, 31
	RGB 12, 28, 09
	RGB 07, 26, 00
	RGB 07, 20, 00

.FirePal:
	RGB 31, 31, 31
	RGB 31, 31, 15
	RGB 31, 24, 04
	RGB 31, 12, 02

.DragonPal:
	RGB 31, 31, 31
	RGB 24, 14, 31
	RGB 19, 06, 31
	RGB 13, 00, 27

.FireBluePal:
	RGB 31, 31, 31
	RGB 24, 31, 31
	RGB 08, 24, 31
	RGB 00, 10, 31

.DragonClawPal:
	RGB 31, 31, 31
	RGB 07, 12, 15
	RGB 31, 05, 00
	RGB 07, 00, 00

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
;            $5 = down-right. Preserves the object's frameset.
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

INCLUDE "data/battle_anims/objects.asm"
