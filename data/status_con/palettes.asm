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

StatsBurnStatusIconPalette:
INCLUDE "gfx/status_con/burn_stats_menu.pal"

StatsFaintedStatusIconPalette:
INCLUDE "gfx/status_con/fainted_stats_menu.pal"

StatsFreezeStatusIconPalette:
INCLUDE "gfx/status_con/freeze_stats_menu.pal"

StatsParalysisStatusIconPalette:
INCLUDE "gfx/status_con/paralysis_stats_menu.pal"

StatsPoisonStatusIconPalette:
INCLUDE "gfx/status_con/poisoned_stats_menu.pal"

StatsSleepStatusIconPalette:
INCLUDE "gfx/status_con/sleep_stats_menu.pal"

StatsToxicStatusIconPalette:
INCLUDE "gfx/status_con/toxic_stats_menu.pal"

StatsStatusIconPalettePointers:
	table_width 2
	dw StatsBurnStatusIconPalette
	dw StatsFaintedStatusIconPalette
	dw StatsFreezeStatusIconPalette
	dw StatsParalysisStatusIconPalette
	dw StatsPoisonStatusIconPalette
	dw StatsSleepStatusIconPalette
	dw StatsToxicStatusIconPalette
	assert_table_length NUM_STATUS_ICONS
