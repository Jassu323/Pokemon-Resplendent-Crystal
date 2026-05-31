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
	ret

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
