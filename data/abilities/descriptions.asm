AbilityDescriptions:
; entries correspond to ability ids (see constants/ability_constants.asm)
	table_width 2
	dw AbilityPlaceholderDescription ; NO_ABILITY
	dw AbilityPlaceholderDescription ; RUN_AWAY
	dw AbilityPlaceholderDescription ; SHED_SKIN
	dw AbilityPlaceholderDescription ; MESMER
	dw AbilityPlaceholderDescription ; VENOM_BOOST
	dw AbilityPlaceholderDescription ; CURSED_BODY
	dw AbilityPlaceholderDescription ; SHORT_FUSE
	dw AbilityPlaceholderDescription ; DAMP
	dw AbilityPlaceholderDescription ; WATER_VEIL
	dw AbilityPlaceholderDescription ; MAGNETISM
	dw AbilityPlaceholderDescription ; SHELL_ARMOR
	dw AbilityPlaceholderDescription ; BATTLE_ARMOR
	dw AbilityPlaceholderDescription ; MULTISCALE
	dw AbilityPlaceholderDescription ; NATURAL_CURE
	dw AbilityPlaceholderDescription ; THERMAL_WAKE
	dw AbilityPlaceholderDescription ; INSOMNIA
	dw AbilityPlaceholderDescription ; STATIC
	dw AbilityPlaceholderDescription ; DRAGON_SKIN
	dw AbilityPlaceholderDescription ; OVERGROW
	dw AbilityPlaceholderDescription ; BLAZE
	dw AbilityPlaceholderDescription ; TORRENT
	dw AbilityPlaceholderDescription ; IRONCLAD
	dw AbilityPlaceholderDescription ; LEVITATE
	dw AbilityPlaceholderDescription ; MARVEL_SCALE
	dw AbilityPlaceholderDescription ; DRIZZLE
	dw AbilityPlaceholderDescription ; DROUGHT
	dw AbilityPlaceholderDescription ; AIR_LOCK
	dw AbilityPlaceholderDescription ; SNOW_WARNING
	dw AbilityPlaceholderDescription ; SLOW_START
	assert_table_length NUM_ABILITIES + 1

AbilityPlaceholderDescription:
	db "placeholder@"
