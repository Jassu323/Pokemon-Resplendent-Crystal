; Battle animation palette loaders and object table kept in bank 63.

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

BattleAnimExt_LoadCustomPal:
	ld a, e
	cp BATTLE_ANIM_WATER_COLUMN_PAL_LOAD
	jp z, .load_water_column
	cp BATTLE_ANIM_GRASS_PAL_LOAD
	jp z, .load_grass
	cp BATTLE_ANIM_FIRE_PAL_LOAD
	jp z, .load_fire
	cp BATTLE_ANIM_DRAGON_PAL_LOAD
	jp z, .load_dragon
	cp BATTLE_ANIM_FIRE_BLUE_PAL_LOAD
	jp z, .load_fire_blue
	cp BATTLE_ANIM_DRAGON_CLAW_PAL_LOAD
	jp z, .load_dragon_claw
	cp BATTLE_ANIM_DRAGON_BLUE_PAL_LOAD
	jp z, .load_dragon_blue
	cp BATTLE_ANIM_WATER_COLUMN_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_GRASS_PAL_RESTORE
	jp z, .restore_green
	cp BATTLE_ANIM_FIRE_PAL_RESTORE
	jp z, .restore_red
	cp BATTLE_ANIM_DRAGON_PAL_RESTORE
	jp z, .restore_red
	cp BATTLE_ANIM_FIRE_BLUE_PAL_RESTORE
	jp z, .restore_red
	cp BATTLE_ANIM_DRAGON_CLAW_PAL_RESTORE
	jp z, .restore_red
	cp BATTLE_ANIM_DRAGON_BLUE_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_THUNDERBOLT_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_GROUND_PAL_LOAD
	jp z, .load_ground
	cp BATTLE_ANIM_GROUND_PAL_RESTORE
	jp z, .restore_brown
	cp BATTLE_ANIM_POISON_PAL_LOAD
	jp z, .load_poison
	cp BATTLE_ANIM_POISON_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_POISON_POWDER_PAL_LOAD
	jp z, .load_poison_powder
	cp BATTLE_ANIM_POISON_POWDER_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_STUN_SPORE_PAL_LOAD
	jp z, .load_stun_spore
	cp BATTLE_ANIM_STUN_SPORE_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_SLEEP_POWDER_PAL_LOAD
	jp z, .load_sleep_powder
	cp BATTLE_ANIM_SLEEP_POWDER_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_SPORE_PAL_LOAD
	jp z, .load_spore
	cp BATTLE_ANIM_SPORE_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_SILVER_WIND_PAL_LOAD
	jp z, .load_silver_wind
	cp BATTLE_ANIM_SILVER_WIND_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_ICE_PAL_LOAD
	jp z, .load_ice
	cp BATTLE_ANIM_ICE_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_WATER_PAL_LOAD
	jr z, .load_water
	cp BATTLE_ANIM_WATER_PAL_RESTORE
	jp z, .restore_blue
	cp BATTLE_ANIM_SHADOW_BALL_PAL_LOAD
	jp z, .load_shadow_ball
	cp BATTLE_ANIM_SHADOW_BALL_PAL_RESTORE
	jp z, .restore_green
	cp BATTLE_ANIM_HYPER_FANG_PAL_LOAD
	jp z, .load_hyper_fang
	cp BATTLE_ANIM_HYPER_FANG_PAL_RESTORE
	jp z, .restore_brown
	ld hl, .ThunderboltPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jp .load_custom_pal

.load_water_column
	ld hl, .WaterColumnPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jp .load_custom_pal

.load_water
	ld hl, .WaterPal
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
	ld de, wOBPals2 palette PAL_BATTLE_OB_RED
	jr .load_custom_pal

.load_ground
	ld hl, .GroundPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BROWN
	jr .load_custom_pal

.load_poison
	ld hl, .PoisonPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_poison_powder
	ld hl, .PoisonPowderPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_stun_spore
	ld hl, .StunSporePal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_sleep_powder
	ld hl, .SleepPowderPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_spore
	ld hl, .SporePal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_silver_wind
	ld hl, .SilverWindPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_ice
	ld hl, .IcePal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BLUE
	jr .load_custom_pal

.load_shadow_ball
	ld hl, .ShadowBallPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_GREEN
	jr .load_custom_pal

.load_hyper_fang
	ld hl, .HyperFangPal
	ld de, wOBPals2 palette PAL_BATTLE_OB_BROWN
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

.restore_brown
	ld hl, wOBPals1 palette PAL_BATTLE_OB_BROWN
	ld de, wOBPals2 palette PAL_BATTLE_OB_BROWN
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

.WaterPal:
	RGB 31, 31, 31
	RGB 17, 19, 31
	RGB 08, 12, 31
	RGB 01, 04, 31

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

.GroundPal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 30, 30, 30 ; white highlight
	RGB 17, 09, 05 ; light brown fill
	RGB 13, 06, 03 ; dark brown border

.PoisonPal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 30, 30, 30 ; white highlight
	RGB 28, 10, 28 ; light purple
	RGB 25, 00, 25 ; mid purple

.PoisonPowderPal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 17, 12, 24 ; lavender
	RGB 28, 10, 28 ; light purple
	RGB 25, 00, 25 ; mid purple

.StunSporePal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 29, 14, 00 ; source lavender -> orange
	RGB 31, 31, 00 ; source light purple -> light yellow
	RGB 31, 27, 00 ; source dark purple -> dark yellow

.SleepPowderPal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 10, 18, 12 ; source lavender -> forest green
	RGB 20, 28, 03 ; source light purple -> yellow-green
	RGB 14, 22, 10 ; source dark purple -> mid-green

.SporePal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 06, 13, 24 ; source lavender -> deep blue
	RGB 10, 22, 31 ; source light purple -> bright cyan-blue
	RGB 08, 17, 28 ; source dark purple -> mid blue

.SilverWindPal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 26, 27, 25 ; bright silver
	RGB 23, 24, 20 ; mid silver
	RGB 20, 21, 15 ; dark silver

.IcePal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 01, 31, 31 ; bright cyan
	RGB 01, 20, 31 ; mid blue
	RGB 01, 04, 31 ; dark blue

.ShadowBallPal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 04, 06, 25 ; light indigo
	RGB 03, 04, 17 ; mid indigo
	RGB 03, 02, 10 ; dark indigo

.HyperFangPal:
	RGB 31, 31, 31 ; transparent (bg)
	RGB 31, 31, 05 ; yellow
	RGB 31, 14, 02 ; orange
	RGB 25, 03, 00 ; red

INCLUDE "data/battle_anims/objects.asm"
