; Pokémon swarms in grass

SwarmGrassWildMons:

; Dunsparce swarm
	map_id DARK_CAVE_VIOLET_ENTRANCE
	db 4 percent, 4 percent, 4 percent ; encounter rates: morn/day/nite
	; morn
	; encounterPercent, SPECIES, minLevel, maxLevel
	dbwbb 30, GEODUDE,       3,  3
	dbwbb 30, DUNSPARCE,     3,  3
	dbwbb 20, ZUBAT,         2,  2
	dbwbb 10, GEODUDE,       2,  2
	dbwbb  5, DUNSPARCE,     2,  2
	dbwbb  4, DUNSPARCE,     4,  4
	dbwbb  1, DUNSPARCE,     4,  4
	; day
	dbwbb 30, GEODUDE,       3,  3
	dbwbb 30, DUNSPARCE,     3,  3
	dbwbb 20, ZUBAT,         2,  2
	dbwbb 10, GEODUDE,       2,  2
	dbwbb  5, DUNSPARCE,     2,  2
	dbwbb  4, DUNSPARCE,     4,  4
	dbwbb  1, DUNSPARCE,     4,  4
	; nite
	dbwbb 30, GEODUDE,       3,  3
	dbwbb 30, DUNSPARCE,     3,  3
	dbwbb 20, ZUBAT,         2,  2
	dbwbb 10, GEODUDE,       2,  2
	dbwbb  5, DUNSPARCE,     2,  2
	dbwbb  4, DUNSPARCE,     4,  4
	dbwbb  1, DUNSPARCE,     4,  4

; Yanma swarm
	map_id ROUTE_35
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	; encounterPercent, SPECIES, minLevel, maxLevel
	dbwbb 30, NIDORAN_M,    12, 12
	dbwbb 30, NIDORAN_F,    12, 12
	dbwbb 20, YANMA,        12, 12
	dbwbb 10, YANMA,        14, 14
	dbwbb  5, PIDGEY,       14, 14
	dbwbb  4, DITTO,        10, 10
	dbwbb  1, DITTO,        10, 10
	; day
	dbwbb 30, NIDORAN_M,    12, 12
	dbwbb 30, NIDORAN_F,    12, 12
	dbwbb 20, YANMA,        12, 12
	dbwbb 10, YANMA,        14, 14
	dbwbb  5, PIDGEY,       14, 14
	dbwbb  4, DITTO,        10, 10
	dbwbb  1, DITTO,        10, 10
	; nite
	dbwbb 30, NIDORAN_M,    12, 12
	dbwbb 30, NIDORAN_F,    12, 12
	dbwbb 20, YANMA,        12, 12
	dbwbb 10, YANMA,        14, 14
	dbwbb  5, HOOTHOOT,     14, 14
	dbwbb  4, DITTO,        10, 10
	dbwbb  1, DITTO,        10, 10

	db -1 ; end
