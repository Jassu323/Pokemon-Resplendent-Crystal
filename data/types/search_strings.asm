PokedexTypeSearchStrings:
; entries correspond with PokedexTypeSearchConversionTable (see data/types/search_types.asm)
	table_width POKEDEX_TYPE_STRING_LENGTH
	db "  ----  @"
	db "  BUG   @"
	db "  DARK  @"
	db " DRAGON @"
	db "ELECTRIC@"
	db " FAIRY  @"
	db "FIGHTING@"
	db "  FIRE  @"
	db " FLYING @"
	db " GHOST  @"
	db " GRASS  @"
	db " GROUND @"
	db "  ICE   @"
	db " NORMAL @"
	db " POISON @"
	db "PSYCHIC @"
	db "  ROCK  @"
	db " STEEL  @"
	db " WATER  @"
	assert_table_length NUM_TYPES + 1
