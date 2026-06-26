; colors of balls thrown in battle

DEF BATTLE_ANIM_BALL_DATA_LENGTH EQU 1 + 1 + 2 + 2

MACRO battle_anim_ball
	db \1
	db BANK(\2)
	dw \2
	dw \3
ENDM

BattleAnimBallData:
	battle_anim_ball POKE_BALL,   PackItemPokeBallIconPalette,   AnimObjBattlePokeBallGFX
	battle_anim_ball GREAT_BALL,  PackItemGreatBallIconPalette,  AnimObjBattleGreatBallGFX
	battle_anim_ball ULTRA_BALL,  PackItemUltraBallIconPalette,  AnimObjBattleUltraBallGFX
	battle_anim_ball MASTER_BALL, PackItemMasterBallIconPalette, AnimObjBattleMasterBallGFX
	battle_anim_ball HEAVY_BALL,  PackItemHeavyBallIconPalette,  AnimObjBattleHeavyBallGFX
	battle_anim_ball LEVEL_BALL,  PackItemLevelBallIconPalette,  AnimObjBattleLevelBallGFX
	battle_anim_ball LURE_BALL,   PackItemLureBallIconPalette,   AnimObjBattleLureBallGFX
	battle_anim_ball FAST_BALL,   PackItemFastBallIconPalette,   AnimObjBattleFastBallGFX
	battle_anim_ball FRIEND_BALL, PackItemFriendBallIconPalette, AnimObjBattleFriendBallGFX
	battle_anim_ball MOON_BALL,   PackItemMoonBallIconPalette,   AnimObjBattleMoonBallGFX
	battle_anim_ball LOVE_BALL,   PackItemLoveBallIconPalette,   AnimObjBattleLoveBallGFX
	battle_anim_ball PARK_BALL,   PackItemParkBallIconPalette,   AnimObjBattleParkBallGFX
	battle_anim_ball -1,          PackItemPokeBallIconPalette,   AnimObjBattlePokeBallGFX

WhitePalette:
	RGB 31, 31, 31
