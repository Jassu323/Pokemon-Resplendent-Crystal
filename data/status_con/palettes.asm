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

BattleStatusIconMainColors:
	table_width 2
	dw palred 30 + palgreen 16 + palblue  6 ; burn
	dw palred 31 + palgreen  0 + palblue  0 ; fainted, unused in battle
	dw palred  6 + palgreen 27 + palblue 26 ; freeze
	dw palred 31 + palgreen 26 + palblue  6 ; paralysis
	dw palred 20 + palgreen  8 + palblue 20 ; poison
	dw palred 21 + palgreen 21 + palblue 15 ; sleep
	dw palred 20 + palgreen  8 + palblue 20 ; toxic
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
