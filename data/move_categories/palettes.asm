PhysicalMoveCategoryIconPalette:
INCLUDE "gfx/move_categories/physical.pal"

SpecialMoveCategoryIconPalette:
INCLUDE "gfx/move_categories/special.pal"

StatusMoveCategoryIconPalette:
INCLUDE "gfx/move_categories/status.pal"


MoveCategoryIconPalettePointers:
	table_width 2
	dw PhysicalMoveCategoryIconPalette
	dw SpecialMoveCategoryIconPalette
	dw StatusMoveCategoryIconPalette
	assert_table_length NUM_MOVE_CATEGORIES