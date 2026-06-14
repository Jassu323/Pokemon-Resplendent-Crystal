MACRO anim_obj_gfx
; # tiles, gfx pointer
	db \1
	dba \2
ENDM

AnimObjGFX:
; entries correspond to BATTLE_ANIM_GFX_* constants
	table_width 4
	anim_obj_gfx  0, AnimObj00GFX
	anim_obj_gfx 21, AnimObjHitGFX
	anim_obj_gfx  6, AnimObjCutGFX
	anim_obj_gfx  6, AnimObjFireGFX
	anim_obj_gfx 20, AnimObjWaterGFX
	anim_obj_gfx 26, AnimObjLightningGFX
	anim_obj_gfx 18, AnimObjPlantGFX
	anim_obj_gfx 12, AnimObjSmokeGFX
	anim_obj_gfx  9, AnimObjExplosionGFX
	anim_obj_gfx 17, AnimObjRocksGFX
	anim_obj_gfx  6, AnimObjIceGFX
	anim_obj_gfx 10, AnimObjPokeBallGFX
	anim_obj_gfx  9, AnimObjPoisonGFX
	anim_obj_gfx 13, AnimObjBubbleGFX
	anim_obj_gfx 16, AnimObjNoiseGFX
	anim_obj_gfx  2, AnimObjPowderGFX
	anim_obj_gfx 11, AnimObjBeamGFX
	anim_obj_gfx  9, AnimObjSpeedGFX
	anim_obj_gfx  9, AnimObjChargeGFX
	anim_obj_gfx 19, AnimObjWindGFX
	anim_obj_gfx 10, AnimObjWhipGFX
	anim_obj_gfx 12, AnimObjEggGFX
	anim_obj_gfx 18, AnimObjRopeGFX
	anim_obj_gfx 13, AnimObjPsychicGFX
	anim_obj_gfx 10, AnimObjReflectGFX
	anim_obj_gfx 27, AnimObjStatusGFX
	anim_obj_gfx 12, AnimObjSandGFX
	anim_obj_gfx 14, AnimObjWebGFX
	anim_obj_gfx 16, AnimObjHazeGFX
	anim_obj_gfx  7, AnimObjHornGFX
	anim_obj_gfx  8, AnimObjFlowerGFX
	anim_obj_gfx 40, AnimObjMiscGFX
	anim_obj_gfx 36, AnimObjSkyAttackGFX
	anim_obj_gfx 16, AnimObjGlobeGFX
	anim_obj_gfx 48, AnimObjShapesGFX
	anim_obj_gfx 18, AnimObjObjectsGFX
	anim_obj_gfx 38, AnimObjShineGFX
	anim_obj_gfx 35, AnimObjAngelsGFX
	anim_obj_gfx 18, AnimObjWaveGFX
	anim_obj_gfx 24, AnimObjAeroblastGFX
	anim_obj_gfx  1, NULL
	anim_obj_gfx  1, NULL
	anim_obj_gfx 24, AnimObjMudBallMediumGFX
	anim_obj_gfx  8, AnimObjThundershockGFX
	anim_obj_gfx 12, AnimObjElectricityEffectGFX
	anim_obj_gfx 51, AnimObjThunderGFX
	anim_obj_gfx 16, AnimObjThunderboltGFX
	anim_obj_gfx 40, AnimObjThunderboltAftereffectGFX
	anim_obj_gfx 48, AnimObjWaterColumnGFX
	anim_obj_gfx 40, AnimObjVineWhipGFX
	anim_obj_gfx 15, AnimObjEmberGFX
	anim_obj_gfx 33, AnimObjDragonClawGFX
	anim_obj_gfx 12, AnimObjPoisonBubbleGFX
	anim_obj_gfx 16, AnimObjShadowBallGFX
	anim_obj_gfx 16, AnimObjSludgeBombGFX
	anim_obj_gfx 12, AnimObjSharpTeethGFX
	anim_obj_gfx 35, AnimObjHyperFangGFX
	anim_obj_gfx 18, AnimObjToxicBubbleGFX
	anim_obj_gfx 16, AnimObjPoisonPowderGFX
	anim_obj_gfx  1, AnimObjSmallBubbleGFX
	anim_obj_gfx  1, AnimObjTinyBubbleGFX
	anim_obj_gfx  4, AnimObjBulletSeedGFX
	anim_obj_gfx 12, AnimObjSilverWindGFX
	anim_obj_gfx 64, AnimObjIceChunkGFX
	anim_obj_gfx 16, AnimObjBlockGFX
	anim_obj_gfx 16, AnimObjForcePalmGFX
	anim_obj_gfx 12, AnimObjFocusPunchGFX
	anim_obj_gfx 36, AnimObjIngrainGFX
	anim_obj_gfx  4, AnimObjMediumBubbleGFX
	anim_obj_gfx  4, AnimObjThoughtBubble1GFX
	anim_obj_gfx 16, AnimObjThoughtBubble2GFX
	anim_obj_gfx 16, AnimObjThoughtBubble3GFX
	anim_obj_gfx 16, AnimObjThoughtBubble4GFX
	anim_obj_gfx 48, AnimObjTauntFingerGFX
	anim_obj_gfx  4, AnimObjTauntAngerGFX
	anim_obj_gfx 32, AnimObjGhostFlameGFX
	anim_obj_gfx 16, AnimObjYawnGFX
	anim_obj_gfx  1, AnimObjSandTombFleckGFX
	anim_obj_gfx  4, AnimObjPinkPetalGFX
	assert_table_length NUM_BATTLE_ANIM_GFX + 1
