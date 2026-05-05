; Palette files for type icons used in the UI
TypeIconPalettes:

NormalTypeIconPalette:
INCLUDE "gfx/types/normal.pal"

FightingTypeIconPalette:
INCLUDE "gfx/types/fighting.pal"

FlyingTypeIconPalette:
INCLUDE "gfx/types/flying.pal"

PoisonTypeIconPalette:
INCLUDE "gfx/types/poison.pal"

GroundTypeIconPalette:
INCLUDE "gfx/types/ground.pal"

RockTypeIconPalette:
INCLUDE "gfx/types/rock.pal"

BugTypeIconPalette:
INCLUDE "gfx/types/bug.pal"

GhostTypeIconPalette:
INCLUDE "gfx/types/ghost.pal"

SteelTypeIconPalette:
INCLUDE "gfx/types/steel.pal"

FireTypeIconPalette:
INCLUDE "gfx/types/fire.pal"

WaterTypeIconPalette:
INCLUDE "gfx/types/water.pal"

GrassTypeIconPalette:
INCLUDE "gfx/types/grass.pal"

ElectricTypeIconPalette:
INCLUDE "gfx/types/electric.pal"

PsychicTypeIconPalette:
INCLUDE "gfx/types/psychic.pal"

IceTypeIconPalette:
INCLUDE "gfx/types/ice.pal"

DragonTypeIconPalette:
INCLUDE "gfx/types/dragon.pal"

DarkTypeIconPalette:
INCLUDE "gfx/types/dark.pal"

FairyTypeIconPalette:
INCLUDE "gfx/types/fairy.pal"

; Pointers for the above palette files
TypeIconPalettePointers:
	; Physical block
	dw NormalTypeIconPalette      ; NORMAL       = 0
	dw FightingTypeIconPalette    ; FIGHTING     = 1
	dw FlyingTypeIconPalette      ; FLYING       = 2
	dw PoisonTypeIconPalette      ; POISON       = 3
	dw GroundTypeIconPalette      ; GROUND       = 4
	dw RockTypeIconPalette        ; ROCK         = 5
	dw NormalTypeIconPalette      ; BIRD         = 6 ; unused/fallback
	dw BugTypeIconPalette         ; BUG          = 7
	dw DarkTypeIconPalette        ; DARK         = 8
	dw SteelTypeIconPalette       ; STEEL        = 9

	; Unused type slots 10-18
	dw NormalTypeIconPalette      ; unused 10
	dw NormalTypeIconPalette      ; unused 11
	dw NormalTypeIconPalette      ; unused 12
	dw NormalTypeIconPalette      ; unused 13
	dw NormalTypeIconPalette      ; unused 14
	dw NormalTypeIconPalette      ; unused 15
	dw NormalTypeIconPalette      ; unused 16
	dw NormalTypeIconPalette      ; unused 17
	dw NormalTypeIconPalette      ; unused 18

	dw GhostTypeIconPalette       ; CURSE_TYPE   = 19 ; fallback

	; Special block
	dw FireTypeIconPalette        ; FIRE         = 20
	dw WaterTypeIconPalette       ; WATER        = 21
	dw GrassTypeIconPalette       ; GRASS        = 22
	dw ElectricTypeIconPalette    ; ELECTRIC     = 23
	dw PsychicTypeIconPalette     ; PSYCHIC_TYPE = 24
	dw IceTypeIconPalette         ; ICE          = 25
	dw DragonTypeIconPalette      ; DRAGON       = 26
	dw GhostTypeIconPalette       ; GHOST        = 27
	dw FairyTypeIconPalette       ; FAIRY        = 28
.end
	ASSERT .end - TypeIconPalettePointers == TYPES_END * 2