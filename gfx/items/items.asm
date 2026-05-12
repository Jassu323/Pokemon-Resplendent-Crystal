PackItemIconTable:
	dbw MASTER_BALL, PackItemMasterBallIconGFX
	dw PackItemMasterBallIconPalette
	dbw ULTRA_BALL, PackItemUltraBallIconGFX
	dw PackItemUltraBallIconPalette
	dbw GREAT_BALL, PackItemGreatBallIconGFX
	dw PackItemGreatBallIconPalette
	dbw POKE_BALL, PackItemPokeBallIconGFX
	dw PackItemPokeBallIconPalette
	dbw POTION, PackItemPotionIconGFX
	dw PackItemPotionIconPalette
	dbw HEAVY_BALL, PackItemHeavyBallIconGFX
	dw PackItemHeavyBallIconPalette
	dbw LEVEL_BALL, PackItemLevelBallIconGFX
	dw PackItemLevelBallIconPalette
	dbw LURE_BALL, PackItemLureBallIconGFX
	dw PackItemLureBallIconPalette
	dbw FAST_BALL, PackItemFastBallIconGFX
	dw PackItemFastBallIconPalette
	dbw FRIEND_BALL, PackItemFriendBallIconGFX
	dw PackItemFriendBallIconPalette
	dbw MOON_BALL, PackItemMoonBallIconGFX
	dw PackItemMoonBallIconPalette
	dbw LOVE_BALL, PackItemLoveBallIconGFX
	dw PackItemLoveBallIconPalette
	db -1

PackItemQuestionIconPalette:
INCLUDE "gfx/items/placeholder.pal"
PackItemEmptyIconPalette:
	RGB 31, 31, 31
	RGB 00, 00, 00
	RGB 00, 00, 00
	RGB 00, 00, 00
PackItemPokeBallIconPalette:
INCLUDE "gfx/items/poke_ball.pal"
PackItemPotionIconPalette:
INCLUDE "gfx/items/potion.pal"
PackItemMasterBallIconPalette:
INCLUDE "gfx/items/master_ball.pal"
PackItemUltraBallIconPalette:
INCLUDE "gfx/items/ultra_ball.pal"
PackItemGreatBallIconPalette:
INCLUDE "gfx/items/great_ball.pal"
PackItemHeavyBallIconPalette:
INCLUDE "gfx/items/heavy_ball.pal"
PackItemLevelBallIconPalette:
INCLUDE "gfx/items/level_ball.pal"
PackItemLureBallIconPalette:
INCLUDE "gfx/items/lure_ball.pal"
PackItemFastBallIconPalette:
INCLUDE "gfx/items/fast_ball.pal"
PackItemFriendBallIconPalette:
INCLUDE "gfx/items/friend_ball.pal"
PackItemMoonBallIconPalette:
INCLUDE "gfx/items/moon_ball.pal"
PackItemLoveBallIconPalette:
INCLUDE "gfx/items/love_ball.pal"
