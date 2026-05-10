BurnFaintedStatusIconPalette:
INCLUDE "gfx/status_con/burn.pal"

FreezeParalysisStatusIconPalette:
INCLUDE "gfx/status_con/freeze.pal"

PoisonSleepStatusIconPalette:
INCLUDE "gfx/status_con/poisoned.pal"

PartyStatusIconPalettePointers:
	table_width 2
	dw BurnFaintedStatusIconPalette
	dw BurnFaintedStatusIconPalette
	dw FreezeParalysisStatusIconPalette
	dw FreezeParalysisStatusIconPalette
	dw PoisonSleepStatusIconPalette
	dw PoisonSleepStatusIconPalette
	dw PoisonSleepStatusIconPalette
	assert_table_length NUM_STATUS_ICONS
