; pokemon ids
; indexes for:
; - PokemonNames (see data/pokemon/names.asm)
; - BaseData (see data/pokemon/base_stats.asm)
; - EvosAttacksPointers (see data/pokemon/evos_attacks_pointers.asm)
; - EggMovePointers (see data/pokemon/egg_move_pointers.asm)
; - PokemonCries (see data/pokemon/cries.asm)
; - MonMenuIcons (see data/pokemon/menu_icons.asm)
; - PokemonPicPointers (see data/pokemon/pic_pointers.asm)
; - PokemonPalettes (see data/pokemon/palettes.asm)
; - PokedexDataPointerTable (see data/pokemon/dex_entry_pointers.asm)
; - AlphabeticalPokedexOrder (see data/pokemon/dex_order_alpha.asm)
; - NewPokedexOrder (see data/pokemon/dex_order_new.asm)
; - Pokered_MonIndices (see data/pokemon/gen1_order.asm)
; - Footprints (see gfx/footprints.asm)
; - AnimationPointers (see gfx/pokemon/anim_pointers.asm)
; - AnimationIdlePointers (see gfx/pokemon/idle_pointers.asm)
; - BitmasksPointers (see gfx/pokemon/bitmask_pointers.asm)
; - FramesPointers (see gfx/pokemon/frame_pointers.asm)
; - EZChat_SortedPokemon (see data/pokemon/ezchat_order.asm)
	const_def 1
	const BULBASAUR  ; 01
	const IVYSAUR    ; 02
	const VENUSAUR   ; 03
	const CHARMANDER ; 04
	const CHARMELEON ; 05
	const CHARIZARD  ; 06
	const SQUIRTLE   ; 07
	const WARTORTLE  ; 08
	const BLASTOISE  ; 09
	const CATERPIE   ; 0a
	const METAPOD    ; 0b
	const BUTTERFREE ; 0c
	const WEEDLE     ; 0d
	const KAKUNA     ; 0e
	const BEEDRILL   ; 0f
	const PIDGEY     ; 10
	const PIDGEOTTO  ; 11
	const PIDGEOT    ; 12
	const RATTATA    ; 13
	const RATICATE   ; 14
	const SPEAROW    ; 15
	const FEAROW     ; 16
	const EKANS      ; 17
	const ARBOK      ; 18
	const PIKACHU    ; 19
	const RAICHU     ; 1a
	const SANDSHREW  ; 1b
	const SANDSLASH  ; 1c
	const NIDORAN_F  ; 1d
	const NIDORINA   ; 1e
	const NIDOQUEEN  ; 1f
	const NIDORAN_M  ; 20
	const NIDORINO   ; 21
	const NIDOKING   ; 22
	const CLEFAIRY   ; 23
	const CLEFABLE   ; 24
	const VULPIX     ; 25
	const NINETALES  ; 26
	const JIGGLYPUFF ; 27
	const WIGGLYTUFF ; 28
	const ZUBAT      ; 29
	const GOLBAT     ; 2a
	const ODDISH     ; 2b
	const GLOOM      ; 2c
	const VILEPLUME  ; 2d
	const PARAS      ; 2e
	const PARASECT   ; 2f
	const VENONAT    ; 30
	const VENOMOTH   ; 31
	const DIGLETT    ; 32
	const DUGTRIO    ; 33
	const MEOWTH     ; 34
	const PERSIAN    ; 35
	const PSYDUCK    ; 36
	const GOLDUCK    ; 37
	const MANKEY     ; 38
	const PRIMEAPE   ; 39
	const GROWLITHE  ; 3a
	const ARCANINE   ; 3b
	const POLIWAG    ; 3c
	const POLIWHIRL  ; 3d
	const POLIWRATH  ; 3e
	const ABRA       ; 3f
	const KADABRA    ; 40
	const ALAKAZAM   ; 41
	const MACHOP     ; 42
	const MACHOKE    ; 43
	const MACHAMP    ; 44
	const BELLSPROUT ; 45
	const WEEPINBELL ; 46
	const VICTREEBEL ; 47
	const TENTACOOL  ; 48
	const TENTACRUEL ; 49
	const GEODUDE    ; 4a
	const GRAVELER   ; 4b
	const GOLEM      ; 4c
	const PONYTA     ; 4d
	const RAPIDASH   ; 4e
	const SLOWPOKE   ; 4f
	const SLOWBRO    ; 50
	const MAGNEMITE  ; 51
	const MAGNETON   ; 52
	const FARFETCH_D ; 53
	const DODUO      ; 54
	const DODRIO     ; 55
	const SEEL       ; 56
	const DEWGONG    ; 57
	const GRIMER     ; 58
	const MUK        ; 59
	const SHELLDER   ; 5a
	const CLOYSTER   ; 5b
	const GASTLY     ; 5c
	const HAUNTER    ; 5d
	const GENGAR     ; 5e
	const ONIX       ; 5f
	const DROWZEE    ; 60
	const HYPNO      ; 61
	const KRABBY     ; 62
	const KINGLER    ; 63
	const VOLTORB    ; 64
	const ELECTRODE  ; 65
	const EXEGGCUTE  ; 66
	const EXEGGUTOR  ; 67
	const CUBONE     ; 68
	const MAROWAK    ; 69
	const HITMONLEE  ; 6a
	const HITMONCHAN ; 6b
	const LICKITUNG  ; 6c
	const KOFFING    ; 6d
	const WEEZING    ; 6e
	const RHYHORN    ; 6f
	const RHYDON     ; 70
	const CHANSEY    ; 71
	const TANGELA    ; 72
	const KANGASKHAN ; 73
	const HORSEA     ; 74
	const SEADRA     ; 75
	const GOLDEEN    ; 76
	const SEAKING    ; 77
	const STARYU     ; 78
	const STARMIE    ; 79
	const MR__MIME   ; 7a
	const SCYTHER    ; 7b
	const JYNX       ; 7c
	const ELECTABUZZ ; 7d
	const MAGMAR     ; 7e
	const PINSIR     ; 7f
	const TAUROS     ; 80
	const MAGIKARP   ; 81
	const GYARADOS   ; 82
	const LAPRAS     ; 83
	const DITTO      ; 84
	const EEVEE      ; 85
	const VAPOREON   ; 86
	const JOLTEON    ; 87
	const FLAREON    ; 88
	const PORYGON    ; 89
	const OMANYTE    ; 8a
	const OMASTAR    ; 8b
	const KABUTO     ; 8c
	const KABUTOPS   ; 8d
	const AERODACTYL ; 8e
	const SNORLAX    ; 8f
	const ARTICUNO   ; 90
	const ZAPDOS     ; 91
	const MOLTRES    ; 92
	const DRATINI    ; 93
	const DRAGONAIR  ; 94
	const DRAGONITE  ; 95
	const MEWTWO     ; 96
	const MEW        ; 97
DEF JOHTO_POKEMON EQU const_value
	const CHIKORITA  ; 98
	const BAYLEEF    ; 99
	const MEGANIUM   ; 9a
	const CYNDAQUIL  ; 9b
	const QUILAVA    ; 9c
	const TYPHLOSION ; 9d
	const TOTODILE   ; 9e
	const CROCONAW   ; 9f
	const FERALIGATR ; a0
	const SENTRET    ; a1
	const FURRET     ; a2
	const HOOTHOOT   ; a3
	const NOCTOWL    ; a4
	const LEDYBA     ; a5
	const LEDIAN     ; a6
	const SPINARAK   ; a7
	const ARIADOS    ; a8
	const CROBAT     ; a9
	const CHINCHOU   ; aa
	const LANTURN    ; ab
	const PICHU      ; ac
	const CLEFFA     ; ad
	const IGGLYBUFF  ; ae
	const TOGEPI     ; af
	const TOGETIC    ; b0
	const NATU       ; b1
	const XATU       ; b2
	const MAREEP     ; b3
	const FLAAFFY    ; b4
	const AMPHAROS   ; b5
	const BELLOSSOM  ; b6
	const MARILL     ; b7
	const AZUMARILL  ; b8
	const SUDOWOODO  ; b9
	const POLITOED   ; ba
	const HOPPIP     ; bb
	const SKIPLOOM   ; bc
	const JUMPLUFF   ; bd
	const AIPOM      ; be
	const SUNKERN    ; bf
	const SUNFLORA   ; c0
	const YANMA      ; c1
	const WOOPER     ; c2
	const QUAGSIRE   ; c3
	const ESPEON     ; c4
	const UMBREON    ; c5
	const MURKROW    ; c6
	const SLOWKING   ; c7
	const MISDREAVUS ; c8
	const UNOWN      ; c9
	const WOBBUFFET  ; ca
	const GIRAFARIG  ; cb
	const PINECO     ; cc
	const FORRETRESS ; cd
	const DUNSPARCE  ; ce
	const GLIGAR     ; cf
	const STEELIX    ; d0
	const SNUBBULL   ; d1
	const GRANBULL   ; d2
	const QWILFISH   ; d3
	const SCIZOR     ; d4
	const SHUCKLE    ; d5
	const HERACROSS  ; d6
	const SNEASEL    ; d7
	const TEDDIURSA  ; d8
	const URSARING   ; d9
	const SLUGMA     ; da
	const MAGCARGO   ; db
	const SWINUB     ; dc
	const PILOSWINE  ; dd
	const CORSOLA    ; de
	const REMORAID   ; df
	const OCTILLERY  ; e0
	const DELIBIRD   ; e1
	const MANTINE    ; e2
	const SKARMORY   ; e3
	const HOUNDOUR   ; e4
	const HOUNDOOM   ; e5
	const KINGDRA    ; e6
	const PHANPY     ; e7
	const DONPHAN    ; e8
	const PORYGON2   ; e9
	const STANTLER   ; ea
	const SMEARGLE   ; eb
	const TYROGUE    ; ec
	const HITMONTOP  ; ed
	const SMOOCHUM   ; ee
	const ELEKID     ; ef
	const MAGBY      ; f0
	const MILTANK    ; f1
	const BLISSEY    ; f2
	const RAIKOU     ; f3
	const ENTEI      ; f4
	const SUICUNE    ; f5
	const LARVITAR   ; f6
	const PUPITAR    ; f7
	const TYRANITAR  ; f8
	const LUGIA      ; f9
	const HO_OH      ; fa
	const CELEBI     ; fb
	const TREECKO    ; fc, NatDex 252
	const GROVYLE    ; fd, NatDex 253
	const SCEPTILE   ; fe, NatDex 254
	const TORCHIC    ; ff, NatDex 255
	const COMBUSKEN  ; 100, NatDex 256
	const BLAZIKEN   ; 101, NatDex 257
	const MUDKIP     ; 102, NatDex 258
	const MARSHTOMP  ; 103, NatDex 259
	const SWAMPERT   ; 104, NatDex 260
	const POOCHYENA  ; 105, NatDex 261
	const MIGHTYENA  ; 106, NatDex 262
	const WINGULL    ; 107, NatDex 278
	const PELIPPER   ; 108, NatDex 279
	const RALTS      ; 109, NatDex 280
	const KIRLIA     ; 10a, NatDex 281
	const GARDEVOIR  ; 10b, NatDex 282
	const GALLADE    ; 10c, NatDex 475
	const SHROOMISH  ; 10d, NatDex 285
	const BRELOOM    ; 10e, NatDex 286
	const MAKUHITA   ; 10f, NatDex 296
	const HARIYAMA   ; 110, NatDex 297
	const SKITTY     ; 111, NatDex 300
	const DELCATTY   ; 112, NatDex 301
	const SABLEYE    ; 113, NatDex 302
	const MAWILE     ; 114, NatDex 303
	const ARON       ; 115, NatDex 304
	const LAIRON     ; 116, NatDex 305
	const AGGRON     ; 117, NatDex 306
	const MEDITITE   ; 118, NatDex 307
	const MEDICHAM   ; 119, NatDex 308
	const ELECTRIKE  ; 11a, NatDex 309
	const MANECTRIC  ; 11b, NatDex 310
	const ROSELIA    ; 11c, NatDex 315
	const ROSERADE   ; 11d, NatDex 407
	const CARVANHA   ; 11e, NatDex 318
	const SHARPEDO   ; 11f, NatDex 319
	const NUMEL      ; 120, NatDex 322
	const CAMERUPT   ; 121, NatDex 323
	const TORKOAL    ; 122, NatDex 324
	const TRAPINCH   ; 123, NatDex 328
	const VIBRAVA    ; 124, NatDex 329
	const FLYGON     ; 125, NatDex 330
	const SWABLU     ; 126, NatDex 333
	const ALTARIA    ; 127, NatDex 334
	const ZANGOOSE   ; 128, NatDex 335
	const SEVIPER    ; 129, NatDex 336
	const LUNATONE   ; 12a, NatDex 337
	const SOLROCK    ; 12b, NatDex 338
	const BARBOACH   ; 12c, NatDex 339
	const WHISCASH   ; 12d, NatDex 340
	const CORPHISH   ; 12e, NatDex 341
	const CRAWDAUNT  ; 12f, NatDex 342
	const BALTOY     ; 130, NatDex 343
	const CLAYDOL    ; 131, NatDex 344
	const LILEEP     ; 132, NatDex 345
	const CRADILY    ; 133, NatDex 346
	const ANORITH    ; 134, NatDex 347
	const ARMALDO    ; 135, NatDex 348
	const FEEBAS     ; 136, NatDex 349
	const MILOTIC    ; 137, NatDex 350
	const SHUPPET    ; 138, NatDex 353
	const BANETTE    ; 139, NatDex 354
	const DUSKULL    ; 13a, NatDex 355
	const DUSCLOPS   ; 13b, NatDex 356
	const DUSKNOIR   ; 13c, NatDex 477
	const ABSOL      ; 13d, NatDex 359
	const SNORUNT    ; 13e, NatDex 361
	const GLALIE     ; 13f, NatDex 362
	const FROSLASS   ; 140, NatDex 478
	const SPHEAL     ; 141, NatDex 363
	const SEALEO     ; 142, NatDex 364
	const WALREIN    ; 143, NatDex 365
	const BAGON      ; 144, NatDex 371
	const SHELGON    ; 145, NatDex 372
	const SALAMENCE  ; 146, NatDex 373
	const BELDUM     ; 147, NatDex 374
	const METANG     ; 148, NatDex 375
	const METAGROSS  ; 149, NatDex 376
	const REGIROCK   ; 14a, NatDex 377
	const REGICE     ; 14b, NatDex 378
	const REGISTEEL  ; 14c, NatDex 379
	const KYOGRE     ; 14d, NatDex 382
	const GROUDON    ; 14e, NatDex 383
	const RAYQUAZA   ; 14f, NatDex 384
	const SHINX      ; 150, NatDex 403
	const LUXIO      ; 151, NatDex 404
	const LUXRAY     ; 152, NatDex 405
	const CRANIDOS   ; 153, NatDex 408
	const RAMPARDOS  ; 154, NatDex 409
	const SHIELDON   ; 155, NatDex 410
	const BASTIODON  ; 156, NatDex 411
	const AMBIPOM    ; 157, NatDex 424
	const BUNEARY    ; 158, NatDex 427
	const LOPUNNY    ; 159, NatDex 428
	const MISMAGIUS  ; 15a, NatDex 429
	const HONCHKROW  ; 15b, NatDex 430
	const BRONZOR    ; 15c, NatDex 436
	const BRONZONG   ; 15d, NatDex 437
	const GIBLE      ; 15e, NatDex 443
	const GABITE     ; 15f, NatDex 444
	const GARCHOMP   ; 160, NatDex 445
	const RIOLU      ; 161, NatDex 447
	const LUCARIO    ; 162, NatDex 448
	const SKORUPI    ; 163, NatDex 451
	const CROAGUNK   ; 164, NatDex 453
	const TOXICROAK  ; 165, NatDex 454
	const SNOVER     ; 166, NatDex 459
	const ABOMASNOW  ; 167, NatDex 460
	const WEAVILE    ; 168, NatDex 461
	const MAGNEZONE  ; 169, NatDex 462
	const LICKILICKY ; 16a, NatDex 463
	const RHYPERIOR  ; 16b, NatDex 464
	const TANGROWTH  ; 16c, NatDex 465
	const TOGEKISS   ; 16d, NatDex 468
	const YANMEGA    ; 16e, NatDex 469
	const LEAFEON    ; 16f, NatDex 470
	const GLACEON    ; 170, NatDex 471
	const GLISCOR    ; 171, NatDex 472
	const MAMOSWINE  ; 172, NatDex 473
	const PORYGON_Z  ; 173, NatDex 474
	const REGIGIGAS  ; 174, NatDex 486
DEF NUM_POKEMON EQU const_value - 1

DEF EGG EQU -3

; limits:
; 999: everything that prints dex counts
; 1407: size of wPokedexOrder
; 4095: hard limit; would require serious redesign to increase
if NUM_POKEMON > 999
	fail "Too many Pokémon defined!"
endc

; Unown forms
; indexes for:
; - UnownWords (see data/pokemon/unown_words.asm)
; - UnownPicPointers (see data/pokemon/unown_pic_pointers.asm)
; - UnownAnimationPointers (see gfx/pokemon/unown_anim_pointers.asm)
; - UnownAnimationIdlePointers (see gfx/pokemon/unown_idle_pointers.asm)
; - UnownBitmasksPointers (see gfx/pokemon/unown_bitmask_pointers.asm)
; - UnownFramesPointers (see gfx/pokemon/unown_frame_pointers.asm)
	const_def 1
	const UNOWN_A ;  01
	const UNOWN_B ;  02
	const UNOWN_C ;  03
	const UNOWN_D ;  04
	const UNOWN_E ;  05
	const UNOWN_F ;  06
	const UNOWN_G ;  07
	const UNOWN_H ;  08
	const UNOWN_I ;  09
	const UNOWN_J ; 0a
	const UNOWN_K ; 0b
	const UNOWN_L ; 0c
	const UNOWN_M ; 0d
	const UNOWN_N ; 0e
	const UNOWN_O ; 0f
	const UNOWN_P ; 10
	const UNOWN_Q ; 11
	const UNOWN_R ; 12
	const UNOWN_S ; 13
	const UNOWN_T ; 14
	const UNOWN_U ; 15
	const UNOWN_V ; 16
	const UNOWN_W ; 17
	const UNOWN_X ; 18
	const UNOWN_Y ; 19
	const UNOWN_Z ; 1a
DEF NUM_UNOWN EQU const_value - 1 ; 26
