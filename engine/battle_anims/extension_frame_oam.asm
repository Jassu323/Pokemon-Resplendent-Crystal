; Extended battle animation framesets and OAM data, kept local to the main animation runtime bank.

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
	ld e, [hl]     ; low byte is already a 0-based index into BattleAnimExtFrameData
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
; entries correspond to BATTLE_ANIM_FRAMESET_* ext constants (bank selector = 1, low byte = 0-based index)
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
	dw .Frameset_ThunderStrikeController ; BATTLE_ANIM_FRAMESET_THUNDER_STRIKE_CONTROLLER
	dw .Frameset_ThunderboltStrike ; BATTLE_ANIM_FRAMESET_THUNDERBOLT_STRIKE
	dw .Frameset_ThunderboltAftereffect ; BATTLE_ANIM_FRAMESET_THUNDERBOLT_AFTEREFFECT
	dw .Frameset_HydroPumpColumn ; BATTLE_ANIM_FRAMESET_HYDRO_PUMP_COLUMN
	dw .Frameset_HydroPumpColumnSlow ; BATTLE_ANIM_FRAMESET_HYDRO_PUMP_COLUMN_SLOW
	dw .Frameset_VineWhip ; BATTLE_ANIM_FRAMESET_VINE_WHIP
	dw .Frameset_DragonClawSlash ; BATTLE_ANIM_FRAMESET_DRAGON_CLAW_SLASH
	dw .Frameset_DragonClawSlashXFlip ; BATTLE_ANIM_FRAMESET_DRAGON_CLAW_SLASH_XFLIP
	dw .Frameset_PoisonBubble ; BATTLE_ANIM_FRAMESET_POISON_BUBBLE
	dw .Frameset_HyperFang ; BATTLE_ANIM_FRAMESET_HYPER_FANG
	dw .Frameset_SludgeBomb ; BATTLE_ANIM_FRAMESET_SLUDGE_BOMB
	dw .Frameset_SludgeBombTargetSplatter ; BATTLE_ANIM_FRAMESET_SLUDGE_BOMB_TARGET_SPLATTER
	dw .Frameset_AcidBubble ; BATTLE_ANIM_FRAMESET_ACID_BUBBLE
	dw .Frameset_AcidDroplet ; BATTLE_ANIM_FRAMESET_ACID_DROPLET
	dw .Frameset_ToxicBubble ; BATTLE_ANIM_FRAMESET_TOXIC_BUBBLE
	dw .Frameset_PoisonPowder ; BATTLE_ANIM_FRAMESET_POISON_POWDER
	dw .Frameset_Hail ; BATTLE_ANIM_FRAMESET_HAIL
	dw .Frameset_SeismicTossLight ; BATTLE_ANIM_FRAMESET_SEISMIC_TOSS_LIGHT
	dw .Frameset_MudBallMedium ; BATTLE_ANIM_FRAMESET_MUD_BALL_MEDIUM
	dw .Frameset_MudSplashMedium ; BATTLE_ANIM_FRAMESET_MUD_SPLASH_MEDIUM
	dw .Frameset_ThundershockStrike ; BATTLE_ANIM_FRAMESET_THUNDERSHOCK_STRIKE
	dw .Frameset_BlizzardWind5A ; BATTLE_ANIM_FRAMESET_BLIZZARD_WIND_5A
	dw .Frameset_BlizzardWind5B ; BATTLE_ANIM_FRAMESET_BLIZZARD_WIND_5B
	dw .Frameset_BlizzardWind5C ; BATTLE_ANIM_FRAMESET_BLIZZARD_WIND_5C
	dw .Frameset_BlizzardWind4 ; BATTLE_ANIM_FRAMESET_BLIZZARD_WIND_4
	dw .Frameset_FairyWind5A ; BATTLE_ANIM_FRAMESET_FAIRY_WIND_5A
	dw .Frameset_FairyWind5B ; BATTLE_ANIM_FRAMESET_FAIRY_WIND_5B
	dw .Frameset_FairyWind5C ; BATTLE_ANIM_FRAMESET_FAIRY_WIND_5C
	dw .Frameset_FairyWind4 ; BATTLE_ANIM_FRAMESET_FAIRY_WIND_4
	dw .Frameset_VampirismFangsUpper ; BATTLE_ANIM_FRAMESET_VAMPIRISM_FANGS_UPPER
	dw .Frameset_VampirismFangsLower ; BATTLE_ANIM_FRAMESET_VAMPIRISM_FANGS_LOWER
	dw .Frameset_BrickBreakWall ; BATTLE_ANIM_FRAMESET_BRICK_BREAK_WALL
	dw .Frameset_BrickBreakShard ; BATTLE_ANIM_FRAMESET_BRICK_BREAK_SHARD
	dw .Frameset_BrickBreakShardXFlip ; BATTLE_ANIM_FRAMESET_BRICK_BREAK_SHARD_XFLIP
	dw .Frameset_BrickBreakShardYFlip ; BATTLE_ANIM_FRAMESET_BRICK_BREAK_SHARD_YFLIP
	dw .Frameset_BrickBreakShardXFlipYFlip ; BATTLE_ANIM_FRAMESET_BRICK_BREAK_SHARD_XFLIP_YFLIP
	dw .Frameset_LeekSlap ; BATTLE_ANIM_FRAMESET_LEEK_SLAP
	assert_table_length NUM_BATTLE_ANIM_EXT_FRAMESETS

.Frameset_ThunderYellow1_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_0, 5
	oamdelete

.Frameset_ThunderYellow1_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_2, 5
	oamdelete

.Frameset_ThunderYellow1_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_0, 5
	oamdelete

.Frameset_ThunderYellow1_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_2, 5
	oamdelete

.Frameset_ThunderPurple_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_0, 5
	oamdelete

.Frameset_ThunderPurple_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_2, 5
	oamdelete

.Frameset_ThunderPurple_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_0, 5
	oamdelete

.Frameset_ThunderPurple_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_2, 5
	oamdelete

.Frameset_ThunderYellow2_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_0, 5
	oamdelete

.Frameset_ThunderYellow2_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_2, 5
	oamdelete

.Frameset_ThunderYellow2_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_0, 5
	oamdelete

.Frameset_ThunderYellow2_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_2, 5
	oamdelete

.Frameset_ThunderOrange_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_0, 5
	oamdelete

.Frameset_ThunderOrange_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_2, 5
	oamdelete

.Frameset_ThunderOrange_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_0, 5
	oamdelete

.Frameset_ThunderOrange_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_2, 5
	oamdelete

.Frameset_ThunderRed_0:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_0, 5
	oamdelete

.Frameset_ThunderRed_1:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_2, 5
	oamdelete

.Frameset_ThunderRed_2:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_0, 5
	oamdelete

.Frameset_ThunderRed_3:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_2, 5
	oamdelete

.Frameset_ThunderStrikeController:
	oamwait 1
	oamrestart

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

.Frameset_PoisonBubble:
	oamframe BATTLE_ANIM_EXT_OAMSET_POISON_BUBBLE, 20
	oamdelete

.Frameset_HyperFang:
	oamframe BATTLE_ANIM_EXT_OAMSET_HYPER_FANG_1, 8
	oamframe BATTLE_ANIM_EXT_OAMSET_HYPER_FANG_2, 16
	oamframe BATTLE_ANIM_EXT_OAMSET_HYPER_FANG_3, 4
	oamframe BATTLE_ANIM_EXT_OAMSET_HYPER_FANG_4, 4
	oamdelete

.Frameset_SludgeBomb:
	oamframe BATTLE_ANIM_EXT_OAMSET_SLUDGE_BOMB, 8
	oamend

.Frameset_SludgeBombTargetSplatter:
	oamframe BATTLE_ANIM_EXT_OAMSET_SLUDGE_BOMB_TARGET_SPLATTER, 20
	oamdelete

.Frameset_AcidBubble:
	oamframe BATTLE_ANIM_EXT_OAMSET_POISON_BUBBLE, 8
	oamend

.Frameset_AcidDroplet:
	oamframe BATTLE_ANIM_EXT_OAMSET_ACID_DROPLET, 8
	oamend

.Frameset_ToxicBubble:
	oamframe BATTLE_ANIM_EXT_OAMSET_TOXIC_BUBBLE_1, 5
	oamframe BATTLE_ANIM_EXT_OAMSET_TOXIC_BUBBLE_2, 5
	oamframe BATTLE_ANIM_EXT_OAMSET_TOXIC_BUBBLE_3, 5
	oamframe BATTLE_ANIM_EXT_OAMSET_TOXIC_BUBBLE_4, 5
	oamdelete

.Frameset_PoisonPowder:
	oamframe BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_CONTROLLER, 1
	oamrestart

.Frameset_Hail:
	oamframe BATTLE_ANIM_EXT_OAMSET_HAIL, 32
	oamend

.Frameset_SeismicTossLight:
	oamframe BATTLE_ANIM_EXT_OAMSET_SEISMIC_TOSS_LIGHT, 8
	oamend

.Frameset_MudBallMedium:
	oamframe BATTLE_ANIM_EXT_OAMSET_MUD_BALL_MEDIUM, 8
	oamend

.Frameset_MudSplashMedium:
	oamframe BATTLE_ANIM_EXT_OAMSET_MUD_SPLASH_MEDIUM_1, 8
	oamframe BATTLE_ANIM_EXT_OAMSET_MUD_SPLASH_MEDIUM_2, 8
	oamdelete

.Frameset_ThundershockStrike:
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_1, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_2, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_3, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_4, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_5, 7
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_LOWER_4, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_LOWER_3, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_LOWER_2, 2
	oamframe BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_LOWER_1, 2
	oamdelete

.Frameset_BlizzardWind5A:
	oamframe BATTLE_ANIM_EXT_OAMSET_BLIZZARD_WIND_5A, 32
	oamend

.Frameset_BlizzardWind5B:
	oamframe BATTLE_ANIM_EXT_OAMSET_BLIZZARD_WIND_5B, 32
	oamend

.Frameset_BlizzardWind5C:
	oamframe BATTLE_ANIM_EXT_OAMSET_BLIZZARD_WIND_5C, 32
	oamend

.Frameset_BlizzardWind4:
	oamframe BATTLE_ANIM_EXT_OAMSET_BLIZZARD_WIND_4, 32
	oamend

.Frameset_FairyWind5A:
	oamframe BATTLE_ANIM_EXT_OAMSET_FAIRY_WIND_5A, 32
	oamend

.Frameset_FairyWind5B:
	oamframe BATTLE_ANIM_EXT_OAMSET_FAIRY_WIND_5B, 32
	oamend

.Frameset_FairyWind5C:
	oamframe BATTLE_ANIM_EXT_OAMSET_FAIRY_WIND_5C, 32
	oamend

.Frameset_FairyWind4:
	oamframe BATTLE_ANIM_EXT_OAMSET_FAIRY_WIND_4, 32
	oamend

.Frameset_VampirismFangsUpper:
	oamframe BATTLE_ANIM_EXT_OAMSET_VAMPIRISM_FANGS_UPPER, 8
	oamend

.Frameset_VampirismFangsLower:
	oamframe BATTLE_ANIM_EXT_OAMSET_VAMPIRISM_FANGS_LOWER, 8
	oamend

.Frameset_BrickBreakWall:
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_77, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_78, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_79, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7A, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7B, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7C, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7D, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_77, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_78, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_79, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7A, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7B, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7C, 1, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7D, 32, B_OAM_XFLIP
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7D, 32, B_OAM_XFLIP
	oamrestart

.Frameset_BrickBreakShard:
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_SHARD, 28
	oamdelete

.Frameset_BrickBreakShardXFlip:
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_SHARD, 28, B_OAM_XFLIP
	oamdelete

.Frameset_BrickBreakShardYFlip:
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_SHARD, 28, B_OAM_YFLIP
	oamdelete

.Frameset_BrickBreakShardXFlipYFlip:
	oamframe BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_SHARD, 28, B_OAM_XFLIP, B_OAM_YFLIP
	oamdelete

.Frameset_LeekSlap:
	oamframe BATTLE_ANIM_EXT_OAMSET_LEEK_SLAP_1, 3
	oamframe BATTLE_ANIM_EXT_OAMSET_LEEK_SLAP_2, 3
	oamframe BATTLE_ANIM_EXT_OAMSET_LEEK_SLAP_3, 3
	oamframe BATTLE_ANIM_EXT_OAMSET_LEEK_SLAP_4, 6
	oamdelete

BattleAnimExtOAMUpdate:
	ld a, e
	cp BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_CONTROLLER
	jp z, BattleAnimRenderPoisonPowderController
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

BattleAnimRenderPoisonPowderController:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld [wBattleAnimTempFrameOAMFlags], a
	ld a, 14
	ld [wBattleAnimTempFixY], a
	ld hl, .Particles

.particle_loop
	ld a, [wBattleAnimTempFrameOAMFlags]
	sub [hl]
	jr c, .skip_particle
	cp POISON_POWDER_PARTICLE_LIFETIME
	jr nc, .skip_particle
	ld [wBattleAnimTempOAMFlags], a
	inc hl
	ld a, [hli]
	ld [wBattleAnimTempXCoord], a
	ld a, [hli]
	ld [wBattleAnimTempYCoord], a
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	push hl
	ld a, [wBattleAnimTempOAMFlags]
	ld l, a
	ld h, 0
	add hl, de
	ld a, [hl]
	ld [wBattleAnimTempYOffset], a
	pop hl
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	push hl
	ld h, d
	ld l, e
	ld d, b
	ld a, [wBattleAnimTempOAMFlags]
	call .GetWobbleOffset
	ld [wBattleAnimTempXOffset], a
	call .ApplyCoords
	call .WriteParticle
	pop hl
	ret c
	jr .done_particle

.skip_particle
	ld de, POISON_POWDER_PARTICLE_ENTRY_LENGTH
	add hl, de

.done_particle
	ld a, [wBattleAnimTempFixY]
	dec a
	ld [wBattleAnimTempFixY], a
	jr nz, .particle_loop
	and a
	ret

.GetWobbleOffset:
; Input: a = local age, d = wave speed, c bit 0 = negate, hl = positive wobble table.
	ld e, a
	ld a, d
	and a
	jr z, .speed0
	dec a
	jr z, .speed1
	dec a
	jr z, .speed2
	ld a, e
	add e
	add e
	jr .got_angle

.speed2
	ld a, e
	add a
	jr .got_angle

.speed1
	ld a, e
	jr .got_angle

.speed0
	xor a

.got_angle
	and $3f
	ld e, a
	ld d, 0
	add hl, de
	ld a, [hl]
	bit 0, c
	ret z
	xor $ff
	inc a
	ret

.ApplyCoords:
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy_coords
	ld a, [wBattleAnimTempXOffset]
	ld b, a
	ld a, [wBattleAnimTempXCoord]
	add b
	ld [wBattleAnimTempXCoord], a
	ld a, [wBattleAnimTempYOffset]
	ld b, a
	ld a, [wBattleAnimTempYCoord]
	add b
	ld [wBattleAnimTempYCoord], a
	ret

.enemy_coords
	ld a, [wBattleAnimTempXCoord]
	ld b, a
	ld a, (-10 * TILE_WIDTH) + 4
	sub b
	ld b, a
	ld a, [wBattleAnimTempXOffset]
	xor $ff
	inc a
	add b
	ld [wBattleAnimTempXCoord], a
	ld a, [wBattleAnimTempYCoord]
	ld b, a
	ld a, $90 - $30 - 6
	sub b
	ld b, a
	ld a, [wBattleAnimTempYOffset]
	add b
	ld [wBattleAnimTempYCoord], a
	ret

.WriteParticle:
	ld a, [wBattleAnimTempOAMFlags]
	ld e, a
	ld d, 0
	ld hl, .FrameTileOffsets
	add hl, de
	ld a, [wBattleAnimTempTileID]
	add BATTLEANIM_BASE_TILE
	add [hl]
	ld b, a
	ld a, [wBattleAnimTempPalette]
	and OAM_PALETTE | OAM_BANK1
	ld c, a
	ld a, [wBattleAnimOAMPointerLo]
	ld e, a
	ld d, HIGH(wShadowOAM)

	ld a, [wBattleAnimTempYCoord]
	sub TILE_WIDTH
	ld [de], a
	inc de
	ld a, [wBattleAnimTempXCoord]
	ld [de], a
	inc de
	ld a, b
	ld [de], a
	inc de
	ld a, c
	ld [de], a
	inc de
	ld a, e
	ld [wBattleAnimOAMPointerLo], a
	cp LOW(wShadowOAMEnd)
	jr nc, .oam_full

	ld a, [wBattleAnimTempYCoord]
	ld [de], a
	inc de
	ld a, [wBattleAnimTempXCoord]
	ld [de], a
	inc de
	ld a, b
	inc a
	ld [de], a
	inc de
	ld a, c
	ld [de], a
	inc de
	ld a, e
	ld [wBattleAnimOAMPointerLo], a
	cp LOW(wShadowOAMEnd)
	jr nc, .oam_full
	and a
	ret

.oam_full
	scf
	ret

DEF POISON_POWDER_PARTICLE_ENTRY_LENGTH EQU 9

.Particles:
; spawn frame, x, y, y table, wobble table, wave speed, flags
	db  0, 106, 34
	dw .Y80, .Wobble5
	db 1, 0
	db  0, 146, 34
	dw .Y80, .Wobble5
	db 1, 1
	db  0, 111, 34
	dw .Y112, .Wobble5
	db 3, 0
	db 15, 131, 34
	dw .Y80, .Wobble5
	db 1, 1
	db 15, 141, 34
	dw .Y96, .Wobble5
	db 1, 0
	db 15, 136, 34
	dw .Y69, .Wobble5
	db 1, 1
	db 15, 121, 34
	dw .Y112, .Wobble5
	db 2, 0
	db 45, 151, 34
	dw .Y80, .Wobble5
	db 1, 1
	db 45, 126, 34
	dw .Y96, .Wobble7
	db 2, 0
	db 45, 131, 34
	dw .Y90, .Wobble8
	db 0, 1
	db 65, 126, 34
	dw .Y80, .Wobble5
	db 1, 1
	db 65, 136, 34
	dw .Y89, .Wobble5
	db 2, 0
	db 65, 156, 34
	dw .Y112, .Wobble8
	db 2, 1
	db 65, 141, 34
	dw .Y80, .Wobble5
	db 1, 0

.FrameTileOffsets:
DEF _pp_n = 0
rept POISON_POWDER_PARTICLE_LIFETIME
	db ((_pp_n / 6) % 8) * 2
	DEF _pp_n += 1
endr

.Y69:
DEF _pp_n = 1
rept POISON_POWDER_PARTICLE_LIFETIME
	db (_pp_n * 69) / $100
	DEF _pp_n += 1
endr

.Y80:
DEF _pp_n = 1
rept POISON_POWDER_PARTICLE_LIFETIME
	db (_pp_n * 80) / $100
	DEF _pp_n += 1
endr

.Y89:
DEF _pp_n = 1
rept POISON_POWDER_PARTICLE_LIFETIME
	db (_pp_n * 89) / $100
	DEF _pp_n += 1
endr

.Y90:
DEF _pp_n = 1
rept POISON_POWDER_PARTICLE_LIFETIME
	db (_pp_n * 90) / $100
	DEF _pp_n += 1
endr

.Y96:
DEF _pp_n = 1
rept POISON_POWDER_PARTICLE_LIFETIME
	db (_pp_n * 96) / $100
	DEF _pp_n += 1
endr

.Y112:
DEF _pp_n = 1
rept POISON_POWDER_PARTICLE_LIFETIME
	db (_pp_n * 112) / $100
	DEF _pp_n += 1
endr

.Wobble5:
	db  0,  0,  0,  1,  1,  2,  2,  3,  3,  3,  4,  4,  4,  4,  4,  4
	db  5,  4,  4,  4,  4,  4,  4,  3,  3,  3,  2,  2,  1,  1,  0,  0
	db  0,  0,  0, -1, -1, -2, -2, -3, -3, -3, -4, -4, -4, -4, -4, -4
	db -5, -4, -4, -4, -4, -4, -4, -3, -3, -3, -2, -2, -1, -1,  0,  0

.Wobble7:
	db  0,  0,  1,  2,  2,  3,  3,  4,  4,  5,  5,  6,  6,  6,  6,  6
	db  7,  6,  6,  6,  6,  6,  5,  5,  4,  4,  3,  3,  2,  2,  1,  0
	db  0,  0, -1, -2, -2, -3, -3, -4, -4, -5, -5, -6, -6, -6, -6, -6
	db -7, -6, -6, -6, -6, -6, -5, -5, -4, -4, -3, -3, -2, -2, -1,  0

.Wobble8:
	db  0,  0,  1,  2,  3,  3,  4,  5,  5,  6,  6,  7,  7,  7,  7,  7
	db  8,  7,  7,  7,  7,  7,  6,  6,  5,  5,  4,  3,  3,  2,  1,  0
	db  0,  0, -1, -2, -3, -3, -4, -5, -5, -6, -6, -7, -7, -7, -7, -7
	db -8, -7, -7, -7, -7, -7, -6, -6, -5, -5, -4, -3, -3, -2, -1,  0

BattleAnimExtOAMData:
; entries correspond to BATTLE_ANIM_EXT_OAMSET_* constants
	table_width 4
	battleanimoam $00,  3, .OAMData_ThunderYellow1A ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_0
	battleanimoam $00,  4, .OAMData_ThunderYellow1B ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_1
	battleanimoam $00,  4, .OAMData_ThunderYellow1C ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_2
	battleanimoam $00,  4, .OAMData_ThunderYellow1B ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_1_3
	battleanimoam $00,  8, .OAMData_ThunderPurpleA ; BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_0
	battleanimoam $00,  8, .OAMData_ThunderPurpleB ; BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_1
	battleanimoam $00,  8, .OAMData_ThunderPurpleC ; BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_2
	battleanimoam $00,  8, .OAMData_ThunderPurpleB ; BATTLE_ANIM_EXT_OAMSET_THUNDER_PURPLE_3
	battleanimoam $00,  6, .OAMData_ThunderYellow2A ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_0
	battleanimoam $00,  8, .OAMData_ThunderYellow2B ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_1
	battleanimoam $00,  8, .OAMData_ThunderYellow2C ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_2
	battleanimoam $00,  8, .OAMData_ThunderYellow2B ; BATTLE_ANIM_EXT_OAMSET_THUNDER_YELLOW_2_3
	battleanimoam $00,  4, .OAMData_ThunderOrangeA ; BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_0
	battleanimoam $00,  4, .OAMData_ThunderOrangeB ; BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_1
	battleanimoam $00,  4, .OAMData_ThunderOrangeC ; BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_2
	battleanimoam $00,  4, .OAMData_ThunderOrangeB ; BATTLE_ANIM_EXT_OAMSET_THUNDER_ORANGE_3
	battleanimoam $00,  2, .OAMData_ThunderRedA ; BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_0
	battleanimoam $00,  3, .OAMData_ThunderRedB ; BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_1
	battleanimoam $00,  4, .OAMData_ThunderRedC ; BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_2
	battleanimoam $00,  3, .OAMData_ThunderRedB ; BATTLE_ANIM_EXT_OAMSET_THUNDER_RED_3
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
	battleanimoam $00, 4, .OAMData_PoisonBubble ; BATTLE_ANIM_EXT_OAMSET_POISON_BUBBLE
	battleanimoam $00,  7, .OAMData_HyperFangFrame1 ; BATTLE_ANIM_EXT_OAMSET_HYPER_FANG_1
	battleanimoam $00, 10, .OAMData_HyperFangFrame2 ; BATTLE_ANIM_EXT_OAMSET_HYPER_FANG_2
	battleanimoam $00, 11, .OAMData_HyperFangFrame3 ; BATTLE_ANIM_EXT_OAMSET_HYPER_FANG_3
	battleanimoam $00,  7, .OAMData_HyperFangFrame4 ; BATTLE_ANIM_EXT_OAMSET_HYPER_FANG_4
	battleanimoam $00, 16, .OAMData_SludgeBomb ; BATTLE_ANIM_EXT_OAMSET_SLUDGE_BOMB
	battleanimoam $08,  4, .OAMData_PoisonBubble ; BATTLE_ANIM_EXT_OAMSET_SLUDGE_BOMB_TARGET_SPLATTER
	battleanimoam $04,  4, .OAMData_PoisonBubble ; BATTLE_ANIM_EXT_OAMSET_ACID_DROPLET
	battleanimoam $00,  2, .OAMData_ToxicBubble1 ; BATTLE_ANIM_EXT_OAMSET_TOXIC_BUBBLE_1
	battleanimoam $02,  4, .OAMData_ToxicBubble2 ; BATTLE_ANIM_EXT_OAMSET_TOXIC_BUBBLE_2
	battleanimoam $06,  6, .OAMData_ToxicBubble3 ; BATTLE_ANIM_EXT_OAMSET_TOXIC_BUBBLE_3
	battleanimoam $0c,  6, .OAMData_ToxicBubble3 ; BATTLE_ANIM_EXT_OAMSET_TOXIC_BUBBLE_4
	battleanimoam $00,  2, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_1
	battleanimoam $02,  2, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_2
	battleanimoam $04,  2, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_3
	battleanimoam $06,  2, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_4
	battleanimoam $08,  2, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_5
	battleanimoam $0a,  2, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_6
	battleanimoam $0c,  2, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_7
	battleanimoam $0e,  2, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_8
	battleanimoam $00,  0, .OAMData_PoisonPowder ; BATTLE_ANIM_EXT_OAMSET_POISON_POWDER_CONTROLLER
	battleanimoam $00, 13, .OAMData_Hail ; BATTLE_ANIM_EXT_OAMSET_HAIL
	battleanimoam $05,  6, .OAMData_SeismicTossLight ; BATTLE_ANIM_EXT_OAMSET_SEISMIC_TOSS_LIGHT
	battleanimoam $00,  4, .OAMData_MudBallMedium ; BATTLE_ANIM_EXT_OAMSET_MUD_BALL_MEDIUM
	battleanimoam $06,  9, .OAMData_MudSplashMedium ; BATTLE_ANIM_EXT_OAMSET_MUD_SPLASH_MEDIUM_1
	battleanimoam $0f,  9, .OAMData_MudSplashMedium ; BATTLE_ANIM_EXT_OAMSET_MUD_SPLASH_MEDIUM_2
	battleanimoam $0f,  9, .OAMData_MudSplashMedium ; BATTLE_ANIM_EXT_OAMSET_MUD_SPLASH_MEDIUM_3
	battleanimoam $00,  2, .OAMData_ThundershockStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_1
	battleanimoam $00,  4, .OAMData_ThundershockStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_2
	battleanimoam $00,  6, .OAMData_ThundershockStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_3
	battleanimoam $00,  8, .OAMData_ThundershockStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_4
	battleanimoam $00, 10, .OAMData_ThundershockStrike ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_5
	battleanimoam $00,  8, .OAMData_ThundershockStrike + 2 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_LOWER_4
	battleanimoam $00,  6, .OAMData_ThundershockStrike + 4 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_LOWER_3
	battleanimoam $00,  4, .OAMData_ThundershockStrike + 6 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_LOWER_2
	battleanimoam $00,  2, .OAMData_ThundershockStrike + 8 * 4 ; BATTLE_ANIM_EXT_OAMSET_THUNDERSHOCK_STRIKE_LOWER_1
	battleanimoam $00,  5, .OAMData_BlizzardWind5A ; BATTLE_ANIM_EXT_OAMSET_BLIZZARD_WIND_5A
	battleanimoam $00,  5, .OAMData_BlizzardWind5B ; BATTLE_ANIM_EXT_OAMSET_BLIZZARD_WIND_5B
	battleanimoam $00,  5, .OAMData_BlizzardWind5C ; BATTLE_ANIM_EXT_OAMSET_BLIZZARD_WIND_5C
	battleanimoam $00,  4, .OAMData_BlizzardWind4 ; BATTLE_ANIM_EXT_OAMSET_BLIZZARD_WIND_4
	battleanimoam $00,  5, .OAMData_FairyWind5A ; BATTLE_ANIM_EXT_OAMSET_FAIRY_WIND_5A
	battleanimoam $00,  5, .OAMData_FairyWind5B ; BATTLE_ANIM_EXT_OAMSET_FAIRY_WIND_5B
	battleanimoam $00,  5, .OAMData_FairyWind5C ; BATTLE_ANIM_EXT_OAMSET_FAIRY_WIND_5C
	battleanimoam $00,  4, .OAMData_FairyWind4 ; BATTLE_ANIM_EXT_OAMSET_FAIRY_WIND_4
	battleanimoam $00, 12, .OAMData_VampirismFangs ; BATTLE_ANIM_EXT_OAMSET_VAMPIRISM_FANGS_UPPER
	battleanimoam $0c, 12, .OAMData_VampirismFangs ; BATTLE_ANIM_EXT_OAMSET_VAMPIRISM_FANGS_LOWER
	battleanimoam $00,  1, .OAMData_BrickBreakWall77 ; BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_77
	battleanimoam $00,  3, .OAMData_BrickBreakWall78 ; BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_78
	battleanimoam $00,  6, .OAMData_BrickBreakWall79 ; BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_79
	battleanimoam $00,  9, .OAMData_BrickBreakWall7A ; BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7A
	battleanimoam $00, 12, .OAMData_BrickBreakWall7B ; BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7B
	battleanimoam $00, 14, .OAMData_BrickBreakWall7C ; BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7C
	battleanimoam $00, 15, .OAMData_BrickBreakWall7D ; BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_WALL_7D
	battleanimoam $00,  2, .OAMData_BrickBreakShard ; BATTLE_ANIM_EXT_OAMSET_BRICK_BREAK_SHARD
	battleanimoam $00,  3, .OAMData_LeekSlap1 ; BATTLE_ANIM_EXT_OAMSET_LEEK_SLAP_1
	battleanimoam $03,  9, .OAMData_LeekSlap2 ; BATTLE_ANIM_EXT_OAMSET_LEEK_SLAP_2
	battleanimoam $0c, 12, .OAMData_LeekSlap3 ; BATTLE_ANIM_EXT_OAMSET_LEEK_SLAP_3
	battleanimoam $18,  4, .OAMData_LeekSlap4 ; BATTLE_ANIM_EXT_OAMSET_LEEK_SLAP_4
	assert_table_length NUM_BATTLE_ANIM_EXT_OAMSETS

.OAMData_BrickBreakWall77:
	dbsprite   1,  -4, 4, 4, $01, OAM_XFLIP | OAM_YFLIP

.OAMData_BrickBreakWall78:
	dbsprite   1,  -4, 4, 4, $00, $0
	dbsprite   0,  -4, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   1,  -3, 4, 4, $01, OAM_XFLIP | OAM_YFLIP

.OAMData_BrickBreakWall79:
	dbsprite   1,  -4, 4, 4, $01, $0
	dbsprite   0,  -4, 4, 4, $00, $0
	dbsprite  -1,  -4, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   1,  -3, 4, 4, $00, $0
	dbsprite   0,  -3, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   1,  -2, 4, 4, $01, OAM_XFLIP | OAM_YFLIP

.OAMData_BrickBreakWall7A:
	dbsprite  -2,  -4, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite  -1,  -4, 4, 4, $00, $0
	dbsprite   0,  -4, 4, 4, $01, $0
	dbsprite  -1,  -3, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   0,  -3, 4, 4, $00, $0
	dbsprite   1,  -3, 4, 4, $01, $0
	dbsprite   0,  -2, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   1,  -2, 4, 4, $00, $0
	dbsprite   1,  -1, 4, 4, $01, OAM_XFLIP | OAM_YFLIP

.OAMData_BrickBreakWall7B:
	dbsprite  -3,  -4, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite  -2,  -4, 4, 4, $00, $0
	dbsprite  -1,  -4, 4, 4, $01, $0
	dbsprite  -2,  -3, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite  -1,  -3, 4, 4, $00, $0
	dbsprite   0,  -3, 4, 4, $01, $0
	dbsprite  -1,  -2, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   0,  -2, 4, 4, $00, $0
	dbsprite   1,  -2, 4, 4, $01, $0
	dbsprite   0,  -1, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   1,  -1, 4, 4, $00, $0
	dbsprite   1,   0, 4, 4, $01, OAM_XFLIP | OAM_YFLIP

.OAMData_BrickBreakWall7C:
	dbsprite  -3,  -4, 4, 4, $00, $0
	dbsprite  -2,  -4, 4, 4, $01, $0
	dbsprite  -3,  -3, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite  -2,  -3, 4, 4, $00, $0
	dbsprite  -1,  -3, 4, 4, $01, $0
	dbsprite  -2,  -2, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite  -1,  -2, 4, 4, $00, $0
	dbsprite   0,  -2, 4, 4, $01, $0
	dbsprite  -1,  -1, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   0,  -1, 4, 4, $00, $0
	dbsprite   1,  -1, 4, 4, $01, $0
	dbsprite   0,   0, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   1,   0, 4, 4, $00, $0
	dbsprite   1,   1, 4, 4, $01, OAM_XFLIP | OAM_YFLIP

.OAMData_BrickBreakWall7D:
	dbsprite  -3,  -4, 4, 4, $01, $0
	dbsprite  -3,  -3, 4, 4, $00, $0
	dbsprite  -2,  -3, 4, 4, $01, $0
	dbsprite  -3,  -2, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite  -2,  -2, 4, 4, $00, $0
	dbsprite  -1,  -2, 4, 4, $01, $0
	dbsprite  -2,  -1, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite  -1,  -1, 4, 4, $00, $0
	dbsprite   0,  -1, 4, 4, $01, $0
	dbsprite  -1,   0, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   0,   0, 4, 4, $00, $0
	dbsprite   1,   0, 4, 4, $01, $0
	dbsprite   0,   1, 4, 4, $01, OAM_XFLIP | OAM_YFLIP
	dbsprite   1,   1, 4, 4, $00, $0
	dbsprite   1,   2, 4, 4, $01, OAM_XFLIP | OAM_YFLIP

.OAMData_BrickBreakShard:
	dbsprite   0,   0, 0, 0, $00, $0
	dbsprite   0,   1, 0, 0, $01, $0

.OAMData_LeekSlap1:
	dbsprite  -2,  -2, 2, 6, $00, $0
	dbsprite  -2,  -1, 2, 6, $01, $0
	dbsprite  -2,   0, 2, 6, $02, $0

.OAMData_LeekSlap2:
	dbsprite  -2,  -2, 3, 5, $00, $0
	dbsprite  -1,  -2, 3, 5, $01, $0
	dbsprite   0,  -2, 3, 5, $02, $0
	dbsprite  -2,  -1, 3, 5, $03, $0
	dbsprite  -1,  -1, 3, 5, $04, $0
	dbsprite   0,  -1, 3, 5, $05, $0
	dbsprite  -2,   0, 3, 5, $06, $0
	dbsprite  -1,   0, 3, 5, $07, $0
	dbsprite   0,   0, 3, 5, $08, $0

.OAMData_LeekSlap3:
	dbsprite  -2,  -2, 2, 7, $00, $0
	dbsprite  -1,  -2, 2, 7, $01, $0
	dbsprite   0,  -2, 2, 7, $02, $0
	dbsprite   1,  -2, 2, 7, $03, $0
	dbsprite  -2,  -1, 2, 7, $04, $0
	dbsprite  -1,  -1, 2, 7, $05, $0
	dbsprite   0,  -1, 2, 7, $06, $0
	dbsprite   1,  -1, 2, 7, $07, $0
	dbsprite  -2,   0, 2, 7, $08, $0
	dbsprite  -1,   0, 2, 7, $09, $0
	dbsprite   0,   0, 2, 7, $0a, $0
	dbsprite   1,   0, 2, 7, $0b, $0

.OAMData_LeekSlap4:
	dbsprite  -1,  -1, 6, 6, $00, $0
	dbsprite   0,  -1, 6, 6, $01, $0
	dbsprite  -1,   0, 6, 6, $02, $0
	dbsprite   0,   0, 6, 6, $03, $0

.OAMData_HyperFangFrame1:
	dbsprite -2, -2, 0, 0, $00, $0
	dbsprite -1, -2, 0, 0, $01, $0
	dbsprite  0, -2, 0, 0, $02, $0
	dbsprite -2, -1, 0, 0, $03, $0
	dbsprite  1,  0, 0, 0, $04, $0
	dbsprite  0,  1, 0, 0, $05, $0
	dbsprite  1,  1, 0, 0, $06, $0

.OAMData_HyperFangFrame2:
	dbsprite -2, -2, 0, 0, $07, $0
	dbsprite -1, -2, 0, 0, $08, $0
	dbsprite  0, -2, 0, 0, $09, $0
	dbsprite -2, -1, 0, 0, $0a, $0
	dbsprite -1, -1, 0, 0, $0b, $0
	dbsprite  0, -1, 0, 0, $0c, $0
	dbsprite -1,  0, 0, 0, $0d, $0
	dbsprite  1,  0, 0, 0, $0e, $0
	dbsprite  0,  1, 0, 0, $0f, $0
	dbsprite  1,  1, 0, 0, $10, $0

.OAMData_HyperFangFrame3:
	dbsprite -2, -2, 0, 0, $11, $0
	dbsprite -1, -2, 0, 0, $12, $0
	dbsprite  0, -2, 0, 0, $13, $0
	dbsprite -2, -1, 0, 0, $14, $0
	dbsprite -1, -1, 0, 0, $15, $0
	dbsprite  0, -1, 0, 0, $16, $0
	dbsprite -1,  0, 0, 0, $17, $0
	dbsprite  1,  0, 0, 0, $18, $0
	dbsprite -1,  1, 0, 0, $19, $0
	dbsprite  0,  1, 0, 0, $1a, $0
	dbsprite  1,  1, 0, 0, $1b, $0

.OAMData_HyperFangFrame4:
	dbsprite  0, -2, 0, 0, $1c, $0
	dbsprite -2, -1, 0, 0, $1d, $0
	dbsprite -1, -1, 0, 0, $1e, $0
	dbsprite  0, -1, 0, 0, $1f, $0
	dbsprite -2,  0, 0, 0, $20, $0
	dbsprite  0,  0, 0, 0, $21, $0
	dbsprite -1,  1, 0, 0, $22, $0

.OAMData_SludgeBomb:
	dbsprite -2, -2, 0, 0, $00, $0
	dbsprite -1, -2, 0, 0, $01, $0
	dbsprite  0, -2, 0, 0, $02, $0
	dbsprite  1, -2, 0, 0, $03, $0
	dbsprite -2, -1, 0, 0, $04, $0
	dbsprite -1, -1, 0, 0, $05, $0
	dbsprite  0, -1, 0, 0, $06, $0
	dbsprite  1, -1, 0, 0, $07, $0
	dbsprite -2,  0, 0, 0, $08, $0
	dbsprite -1,  0, 0, 0, $09, $0
	dbsprite  0,  0, 0, 0, $0a, $0
	dbsprite  1,  0, 0, 0, $0b, $0
	dbsprite -2,  1, 0, 0, $0c, $0
	dbsprite -1,  1, 0, 0, $0d, $0
	dbsprite  0,  1, 0, 0, $0e, $0
	dbsprite  1,  1, 0, 0, $0f, $0

.OAMData_ThunderYellow1A:
	dbsprite   0, 0, 0, 0, $00, $0
	dbsprite  -1, 1, 0, 0, $01, $0
	dbsprite   0, 1, 0, 0, $02, $0

.OAMData_ThunderYellow1B:
	dbsprite  -1, 0, 0, 0, $01, $0
	dbsprite   0, 0, 0, 0, $02, $0
	dbsprite  -1, 1, 0, 0, $03, $0
	dbsprite   0, 1, 0, 0, $04, $0

.OAMData_ThunderYellow1C:
	dbsprite  -1, 0, 0, 0, $03, $0
	dbsprite   0, 0, 0, 0, $04, $0
	dbsprite  -1, 1, 0, 0, $05, $0
	dbsprite   0, 1, 0, 0, $06, $0

.OAMData_ThunderPurpleA:
	dbsprite  -2, 0, 0, 0, $07, $0
	dbsprite  -1, 0, 0, 0, $08, $0
	dbsprite   0, 0, 0, 0, $09, $0
	dbsprite   1, 0, 0, 0, $0a, $0
	dbsprite  -2, 1, 0, 0, $0b, $0
	dbsprite  -1, 1, 0, 0, $0c, $0
	dbsprite   0, 1, 0, 0, $0d, $0
	dbsprite   1, 1, 0, 0, $0e, $0

.OAMData_ThunderPurpleB:
	dbsprite  -2, 0, 0, 0, $0b, $0
	dbsprite  -1, 0, 0, 0, $0c, $0
	dbsprite   0, 0, 0, 0, $0d, $0
	dbsprite   1, 0, 0, 0, $0e, $0
	dbsprite  -2, 1, 0, 0, $0f, $0
	dbsprite  -1, 1, 0, 0, $10, $0
	dbsprite   0, 1, 0, 0, $11, $0
	dbsprite   1, 1, 0, 0, $12, $0

.OAMData_ThunderPurpleC:
	dbsprite  -2, 0, 0, 0, $0f, $0
	dbsprite  -1, 0, 0, 0, $10, $0
	dbsprite   0, 0, 0, 0, $11, $0
	dbsprite   1, 0, 0, 0, $12, $0
	dbsprite  -2, 1, 0, 0, $13, $0
	dbsprite  -1, 1, 0, 0, $14, $0
	dbsprite   0, 1, 0, 0, $15, $0
	dbsprite   1, 1, 0, 0, $16, $0

.OAMData_ThunderYellow2A:
	dbsprite  -1, 0, 0, 0, $17, $0
	dbsprite   0, 0, 0, 0, $18, $0
	dbsprite  -2, 1, 0, 0, $19, $0
	dbsprite  -1, 1, 0, 0, $1a, $0
	dbsprite   0, 1, 0, 0, $1b, $0
	dbsprite   1, 1, 0, 0, $1c, $0

.OAMData_ThunderYellow2B:
	dbsprite  -2, 0, 0, 0, $19, $0
	dbsprite  -1, 0, 0, 0, $1a, $0
	dbsprite   0, 0, 0, 0, $1b, $0
	dbsprite   1, 0, 0, 0, $1c, $0
	dbsprite  -2, 1, 0, 0, $1d, $0
	dbsprite  -1, 1, 0, 0, $1e, $0
	dbsprite   0, 1, 0, 0, $1f, $0
	dbsprite   1, 1, 0, 0, $20, $0

.OAMData_ThunderYellow2C:
	dbsprite  -2, 0, 0, 0, $1d, $0
	dbsprite  -1, 0, 0, 0, $1e, $0
	dbsprite   0, 0, 0, 0, $1f, $0
	dbsprite   1, 0, 0, 0, $20, $0
	dbsprite  -2, 1, 0, 0, $21, $0
	dbsprite  -1, 1, 0, 0, $22, $0
	dbsprite   0, 1, 0, 0, $23, $0
	dbsprite   1, 1, 0, 0, $24, $0

.OAMData_ThunderOrangeA:
	dbsprite  -1, 0, 0, 0, $25, $0
	dbsprite   0, 0, 0, 0, $26, $0
	dbsprite  -1, 1, 0, 0, $27, $0
	dbsprite   0, 1, 0, 0, $28, $0

.OAMData_ThunderOrangeB:
	dbsprite  -1, 0, 0, 0, $27, $0
	dbsprite   0, 0, 0, 0, $28, $0
	dbsprite  -1, 1, 0, 0, $29, $0
	dbsprite   0, 1, 0, 0, $2a, $0

.OAMData_ThunderOrangeC:
	dbsprite  -1, 0, 0, 0, $29, $0
	dbsprite   0, 0, 0, 0, $2a, $0
	dbsprite  -1, 1, 0, 0, $2b, $0
	dbsprite   0, 1, 0, 0, $2c, $0

.OAMData_ThunderRedA:
	dbsprite  -1, 0, 0, 0, $2d, $0
	dbsprite  -1, 1, 0, 0, $2e, $0

.OAMData_ThunderRedB:
	dbsprite  -1, 0, 0, 0, $2e, $0
	dbsprite  -1, 1, 0, 0, $2f, $0
	dbsprite   0, 1, 0, 0, $30, $0

.OAMData_ThunderRedC:
	dbsprite  -1, 0, 0, 0, $2f, $0
	dbsprite   0, 0, 0, 0, $30, $0
	dbsprite  -1, 1, 0, 0, $31, $0
	dbsprite   0, 1, 0, 0, $32, $0

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

.OAMData_PoisonBubble:
	dbsprite -1, -1, 0, 0, $00, $0
	dbsprite  0, -1, 0, 0, $01, $0
	dbsprite -1,  0, 0, 0, $02, $0
	dbsprite  0,  0, 0, 0, $03, $0

.OAMData_ToxicBubble1:
	dbsprite -1,  0, 0, 0, $00, $0
	dbsprite  0,  0, 0, 0, $01, $0

.OAMData_ToxicBubble2:
	dbsprite -1, -1, 0, 0, $00, $0
	dbsprite  0, -1, 0, 0, $01, $0
	dbsprite -1,  0, 0, 0, $02, $0
	dbsprite  0,  0, 0, 0, $03, $0

.OAMData_ToxicBubble3:
	dbsprite -1, -2, 0, 0, $00, $0
	dbsprite  0, -2, 0, 0, $01, $0
	dbsprite -1, -1, 0, 0, $02, $0
	dbsprite  0, -1, 0, 0, $03, $0
	dbsprite -1,  0, 0, 0, $04, $0
	dbsprite  0,  0, 0, 0, $05, $0

.OAMData_PoisonPowder:
	dbsprite  0, -1, 0, 0, $00, $0
	dbsprite  0,  0, 0, 0, $01, $0

.OAMData_Hail:
	dbsprite -13,  -2, 4, 0, $04, $0
	dbsprite -11,  -4, 4, 0, $04, $0
	dbsprite  -9,  -1, 4, 0, $04, $0
	dbsprite  -7,  -5, 4, 0, $04, $0
	dbsprite  -5,  -3, 4, 0, $04, $0
	dbsprite  -3,  -5, 4, 0, $04, $0
	dbsprite  -1,  -3, 4, 0, $04, $0
	dbsprite   0,  -3, 4, 0, $04, $0
	dbsprite   2,  -5, 4, 0, $04, $0
	dbsprite   4,   0, 4, 0, $04, $0
	dbsprite   6,  -2, 4, 0, $04, $0
	dbsprite   8,  -4, 4, 0, $04, $0
	dbsprite  10,  -2, 4, 0, $04, $0

.OAMData_BlizzardWind5A:
	dbsprite -18,  -8, 4, 0, $04, $0
	dbsprite -11,  -6, 4, 0, $04, $0
	dbsprite  -3,  -4, 4, 0, $04, $0
	dbsprite   6,  -2, 4, 0, $04, $0
	dbsprite  14,   1, 4, 0, $04, $0

.OAMData_BlizzardWind5B:
	dbsprite -15,  -7, 4, 0, $04, $0
	dbsprite  -8,  -5, 4, 0, $04, $0
	dbsprite   0,  -3, 4, 0, $04, $0
	dbsprite   8,  -1, 4, 0, $04, $0
	dbsprite  16,   0, 4, 0, $04, $0

.OAMData_BlizzardWind5C:
	dbsprite -20,  -6, 4, 0, $04, $0
	dbsprite -13,  -4, 4, 0, $04, $0
	dbsprite  -5,  -2, 4, 0, $04, $0
	dbsprite   4,   0, 4, 0, $04, $0
	dbsprite  12,  -7, 4, 0, $04, $0

.OAMData_BlizzardWind4:
	dbsprite -17,  -5, 4, 0, $04, $0
	dbsprite  -9,  -3, 4, 0, $04, $0
	dbsprite   2,  -1, 4, 0, $04, $0
	dbsprite  15,   1, 4, 0, $04, $0

.OAMData_FairyWind5A:
	dbsprite -18,  -8, 4, 0, $00, $0
	dbsprite -11,  -6, 4, 0, $00, $0
	dbsprite  -3,  -4, 4, 0, $00, $0
	dbsprite   6,  -2, 4, 0, $00, $0
	dbsprite  14,   1, 4, 0, $00, $0

.OAMData_FairyWind5B:
	dbsprite -15,  -7, 4, 0, $00, $0
	dbsprite  -8,  -5, 4, 0, $00, $0
	dbsprite   0,  -3, 4, 0, $00, $0
	dbsprite   8,  -1, 4, 0, $00, $0
	dbsprite  16,   0, 4, 0, $00, $0

.OAMData_FairyWind5C:
	dbsprite -20,  -6, 4, 0, $00, $0
	dbsprite -13,  -4, 4, 0, $00, $0
	dbsprite  -5,  -2, 4, 0, $00, $0
	dbsprite   4,   0, 4, 0, $00, $0
	dbsprite  12,  -7, 4, 0, $00, $0

.OAMData_FairyWind4:
	dbsprite -17,  -5, 4, 0, $00, $0
	dbsprite  -9,  -3, 4, 0, $00, $0
	dbsprite   2,  -1, 4, 0, $00, $0
	dbsprite  15,   1, 4, 0, $00, $0

.OAMData_VampirismFangs:
	dbsprite -2, -1, 0, 0, $00, $0
	dbsprite -1, -1, 0, 0, $01, $0
	dbsprite  0, -1, 0, 0, $02, $0
	dbsprite  1, -1, 0, 0, $03, $0
	dbsprite -2,  0, 0, 0, $04, $0
	dbsprite -1,  0, 0, 0, $05, $0
	dbsprite  0,  0, 0, 0, $06, $0
	dbsprite  1,  0, 0, 0, $07, $0
	dbsprite -2,  1, 0, 0, $08, $0
	dbsprite -1,  1, 0, 0, $09, $0
	dbsprite  0,  1, 0, 0, $0a, $0
	dbsprite  1,  1, 0, 0, $0b, $0

.OAMData_SeismicTossLight:
	dbsprite   0,   0, 0, 0, $00, $0
	dbsprite   3,   0, 0, 4, $00, $0
	dbsprite   6,  -1, 0, 4, $00, $0
	dbsprite   9,   0, 0, 2, $00, $0
	dbsprite  12,   0, 0, 6, $00, $0
	dbsprite  15,  -1, 0, 0, $00, $0

.OAMData_MudBallMedium:
	dbsprite  -1,  -1, 0, 0, $00, $0
	dbsprite   0,  -1, 0, 0, $01, $0
	dbsprite  -1,   0, 0, 0, $03, $0
	dbsprite   0,   0, 0, 0, $04, $0

.OAMData_MudSplashMedium:
	dbsprite  -1,  -1, 0, 0, $00, $0
	dbsprite   0,  -1, 0, 0, $01, $0
	dbsprite   1,  -1, 0, 0, $02, $0
	dbsprite  -1,   0, 0, 0, $03, $0
	dbsprite   0,   0, 0, 0, $04, $0
	dbsprite   1,   0, 0, 0, $05, $0
	dbsprite  -1,   1, 0, 0, $06, $0
	dbsprite   0,   1, 0, 0, $07, $0
	dbsprite   1,   1, 0, 0, $08, $0

.OAMData_ThundershockStrike:
	dbsprite   0,  -7, 0, 0, $00, $0
	dbsprite   0,  -6, 0, 0, $01, $0
	dbsprite   0,  -5, 0, 0, $02, $0
	dbsprite   0,  -4, 0, 0, $03, $0
	dbsprite   0,  -3, 0, 0, $04, $0
	dbsprite   0,  -2, 0, 0, $05, $0
	dbsprite   0,  -1, 0, 0, $06, $0
	dbsprite   0,   0, 0, 0, $07, $0
	dbsprite   0,   1, 0, 0, $00, $0
	dbsprite   0,   2, 0, 0, $01, $0
