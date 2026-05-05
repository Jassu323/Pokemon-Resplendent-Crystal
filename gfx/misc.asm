SECTION "Trainer Backpics", ROMX

ChrisBackpic::
INCBIN "gfx/player/chris_back.2bpp.lz"
DudeBackpic::
INCBIN "gfx/battle/dude.2bpp.lz"


SECTION "Shrink Pics", ROMX

Shrink1Pic::
INCBIN "gfx/new_game/shrink1.2bpp.lz"
Shrink2Pic::
INCBIN "gfx/new_game/shrink2.2bpp.lz"


SECTION "Unused Egg Pic", ROMX

UnusedEggPic::
; The G/S Egg pic. This is shifted up a few pixels.
INCBIN "gfx/pokemon/egg/unused_front.2bpp.lz"


SECTION "The End", ROMX

TheEndGFX::
INCBIN "gfx/credits/theend.2bpp"


SECTION "Font Inversed", ROMX

FontInversed::
INCBIN "gfx/font/font_inversed.1bpp"


SECTION "Copyright", ROMX

CopyrightGFX::
INCBIN "gfx/splash/copyright.2bpp"


SECTION "Intro Logo", ROMX

GameFreakDittoGFX::
INCBIN "gfx/splash/ditto.2bpp.lz"


SECTION "Unown Font", ROMX

UnownFont::
INCBIN "gfx/font/unown_font.2bpp"


SECTION "Pokégear GFX", ROMX

PokegearGFX::
INCBIN "gfx/pokegear/pokegear.2bpp.lz"

SECTION "Type Icons", ROMX

NormalTypeIconGFX::
INCBIN "gfx/types/normal.2bpp"

FightingTypeIconGFX::
INCBIN "gfx/types/fighting.2bpp"

FlyingTypeIconGFX::
INCBIN "gfx/types/flying.2bpp"

PoisonTypeIconGFX::
INCBIN "gfx/types/poison.2bpp"

GroundTypeIconGFX::
INCBIN "gfx/types/ground.2bpp"

RockTypeIconGFX::
INCBIN "gfx/types/rock.2bpp"

BugTypeIconGFX::
INCBIN "gfx/types/bug.2bpp"

GhostTypeIconGFX::
INCBIN "gfx/types/ghost.2bpp"

SteelTypeIconGFX::
INCBIN "gfx/types/steel.2bpp"

FireTypeIconGFX::
INCBIN "gfx/types/fire.2bpp"

WaterTypeIconGFX::
INCBIN "gfx/types/water.2bpp"

GrassTypeIconGFX::
INCBIN "gfx/types/grass.2bpp"

ElectricTypeIconGFX::
INCBIN "gfx/types/electric.2bpp"

PsychicTypeIconGFX::
INCBIN "gfx/types/psychic.2bpp"

IceTypeIconGFX::
INCBIN "gfx/types/ice.2bpp"

DragonTypeIconGFX::
INCBIN "gfx/types/dragon.2bpp"

DarkTypeIconGFX::
INCBIN "gfx/types/dark.2bpp"

FairyTypeIconGFX::
INCBIN "gfx/types/fairy.2bpp"

/* TypeIconGFXPointers::
	; Physical-ish block
	dba NormalTypeIconGFX      ; NORMAL       = 0
	dba FightingTypeIconGFX    ; FIGHTING     = 1
	dba FlyingTypeIconGFX      ; FLYING       = 2
	dba PoisonTypeIconGFX      ; POISON       = 3
	dba GroundTypeIconGFX      ; GROUND       = 4
	dba RockTypeIconGFX        ; ROCK         = 5
	dba NormalTypeIconGFX      ; BIRD         = 6 ; unused/fallback
	dba BugTypeIconGFX         ; BUG          = 7
	dba GhostTypeIconGFX       ; GHOST        = 8
	dba SteelTypeIconGFX       ; STEEL        = 9

	; Unused type slots 10-18
	dba NormalTypeIconGFX      ; unused 10
	dba NormalTypeIconGFX      ; unused 11
	dba NormalTypeIconGFX      ; unused 12
	dba NormalTypeIconGFX      ; unused 13
	dba NormalTypeIconGFX      ; unused 14
	dba NormalTypeIconGFX      ; unused 15
	dba NormalTypeIconGFX      ; unused 16
	dba NormalTypeIconGFX      ; unused 17
	dba NormalTypeIconGFX      ; unused 18

	dba GhostTypeIconGFX       ; CURSE_TYPE   = 19 ; fallback

	; Special-ish block
	dba FireTypeIconGFX        ; FIRE         = 20
	dba WaterTypeIconGFX       ; WATER        = 21
	dba GrassTypeIconGFX       ; GRASS        = 22
	dba ElectricTypeIconGFX    ; ELECTRIC     = 23
	dba PsychicTypeIconGFX     ; PSYCHIC_TYPE = 24
	dba IceTypeIconGFX         ; ICE          = 25
	dba DragonTypeIconGFX      ; DRAGON       = 26
	dba DarkTypeIconGFX        ; DARK         = 27
	dba FairyTypeIconGFX       ; FAIRY        = 28
.end
	ASSERT .end - TypeIconGFXPointers == TYPES_END * 3 */
