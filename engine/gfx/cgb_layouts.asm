; Replaces the functionality of sgb.asm to work with CGB hardware.

CheckCGB:
	ldh a, [hCGB]
	and a
	ret

LoadSGBLayoutCGB:
	ld a, b
	cp SCGB_DEFAULT
	jr nz, .not_default
	ld a, [wDefaultSGBLayout]
.not_default
	cp SCGB_PARTY_MENU_HP_BARS
	jp z, CGB_ApplyPartyMenuHPPals
	call ResetBGPals
	ld l, a
	ld h, 0
	add hl, hl
	ld de, CGBLayoutJumptable
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld de, .done
	push de
	jp hl
.done:
	ret

CGBLayoutJumptable:
; entries correspond to SCGB_* constants (see constants/scgb_constants.asm)
	table_width 2
	dw _CGB_BattleGrayscale
	dw _CGB_BattleColors
	dw _CGB_PokegearPals
	dw _CGB_StatsScreenHPPals
	dw _CGB_Pokedex
	dw _CGB_SlotMachine
	dw _CGB_BetaTitleScreen
	dw _CGB_GSIntro
	dw _CGB_Diploma
	dw _CGB_MapPals
	dw _CGB_PartyMenu
	dw _CGB_Evolution
	dw _CGB_GSTitleScreen
	dw _CGB_Unused0D
	dw _CGB_MoveList
	dw _CGB_BetaPikachuMinigame
	dw _CGB_PokedexSearchOption
	dw _CGB_BetaPoker
	dw _CGB_Pokepic
	dw _CGB_MagnetTrain
	dw _CGB_PackPals
	dw _CGB_TrainerCard
	dw _CGB_TrainerCardKanto
	dw _CGB_PokedexUnownMode
	dw _CGB_BillsPC
	dw _CGB_UnownPuzzle
	dw _CGB_GamefreakLogo
	dw _CGB_PlayerOrMonFrontpicPals
	dw _CGB_TradeTube
	dw _CGB_TrainerOrMonFrontpicPals
	dw _CGB_Unused1E
	dw _CGB_Unused1E
	assert_table_length NUM_SCGB_LAYOUTS

_CGB_BattleGrayscale:
	ld hl, PalPacket_BattleGrayscale + 1
	ld de, wBGPals1
	ld c, 4
	call CopyPalettes
	ld hl, PalPacket_BattleGrayscale + 1
	ld de, wBGPals1 palette PAL_BATTLE_BG_EXP
	ld c, 4
	call CopyPalettes
	ld hl, PalPacket_BattleGrayscale + 1
	ld de, wOBPals1
	ld c, 2
	call CopyPalettes
	jp _CGB_FinishBattleScreenLayout

_CGB_BattleColors:
	call CGB_LoadBattleColorPalettes
	call ApplyPals
	jp _CGB_FinishBattleScreenLayout

CGB_PrepareBattleScreenLayoutNoApply::
	ldh a, [hCGB]
	and a
	ret z
	call CGB_LoadBattleColorPalettes
	jp CGB_FillBattleScreenAttrmap

CGB_LoadBattleColorPalettes:
	ld de, wBGPals1
	call GetBattlemonBackpicPalettePointer
	push hl
	call LoadPalette_White_Col1_Col2_Black ; PAL_BATTLE_BG_PLAYER
	call GetEnemyFrontpicPalettePointer
	push hl
	call LoadPalette_White_Col1_Col2_Black ; PAL_BATTLE_BG_ENEMY
	ld a, [wEnemyHPPal]
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	ld bc, HPBarPals
	add hl, bc
	call LoadPalette_White_Col1_Col2_Black ; PAL_BATTLE_BG_ENEMY_HP
	ld a, [wPlayerHPPal]
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	ld bc, HPBarPals
	add hl, bc
	call LoadPalette_White_Col1_Col2_Black ; PAL_BATTLE_BG_PLAYER_HP
	ld hl, ExpBarPalette
	call LoadPalette_White_Col1_Col2_Black ; PAL_BATTLE_BG_EXP
	call LoadBattleStatusIconPaletteForBattleLayout
	call CGB_LoadBattleHUDGenderPalettes
	ld de, wOBPals1
	pop hl
	call LoadPalette_White_Col1_Col2_Black ; PAL_BATTLE_OB_ENEMY
	pop hl
	call LoadPalette_White_Col1_Col2_Black ; PAL_BATTLE_OB_PLAYER
	ld a, SCGB_BATTLE_COLORS
	ld [wDefaultSGBLayout], a
	ret

CGB_LoadBattleHUDGenderPalettes:
	ld a, [wCurPartySpecies]
	push af
	ld a, [wCurSpecies]
	push af
	ld a, [wMonType]
	push af
	ld a, [wTempMonDVs]
	push af
	ld a, [wTempMonDVs + 1]
	push af
	call .Enemy
	call .Player
	pop af
	ld [wTempMonDVs + 1], a
	pop af
	ld [wTempMonDVs], a
	pop af
	ld [wMonType], a
	pop af
	ld [wCurSpecies], a
	pop af
	ld [wCurPartySpecies], a
	ret

.Enemy
	ld a, [wTempEnemyMonSpecies]
	and a
	jr z, .enemy_genderless
	ld [wCurPartySpecies], a
	ld [wCurSpecies], a
	ld hl, wEnemyMonDVs
	ld a, [wEnemySubStatus5]
	bit SUBSTATUS_TRANSFORMED, a
	jr z, .got_enemy_dvs
	ld hl, wEnemyBackupDVs

.got_enemy_dvs
	call .CopyDVs
	call .GetGenderColor
	jr .copy_enemy

.enemy_genderless
	ld hl, .genderless

.copy_enemy
	ld de, wBGPals1 palette PAL_BATTLE_BG_ENEMY_HP color 1
	ld bc, wBGPals2 palette PAL_BATTLE_BG_ENEMY_HP color 1
	jr .copy_to_both

.Player
	ld a, [wBattleMonSpecies]
	and a
	jr z, .player_genderless
	ld [wCurPartySpecies], a
	ld [wCurSpecies], a
	ld hl, wBattleMonDVs
	call .CopyDVs
	call .GetGenderColor
	jr .copy_player

.player_genderless
	ld hl, .genderless

.copy_player
	ld de, wBGPals1 palette PAL_BATTLE_BG_PLAYER_HP color 1
	ld bc, wBGPals2 palette PAL_BATTLE_BG_PLAYER_HP color 1
	jr .copy_to_both

.GetGenderColor
	ld a, TEMPMON
	ld [wMonType], a
	callfar GetGender
	ld hl, .genderless
	ret c
	ld hl, .male_color
	ret nz

.female
	ld hl, .female_color
	ret

.copy
	ld a, [hli]
	ld [de], a
	inc de
	ld a, [hl]
	ld [de], a
	ret

.copy_to_both
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rWBK], a
	push hl
	call .copy
	pop hl
	ld d, b
	ld e, c
	call .copy
	pop af
	ldh [rWBK], a
	ret

.CopyDVs
	ld a, [hli]
	ld [wTempMonDVs], a
	ld a, [hl]
	ld [wTempMonDVs + 1], a
	ret

.genderless
	RGB 31, 25, 00
.male_color
	RGB 04, 13, 31
.female_color
	RGB 31, 07, 12

_CGB_FinishBattleScreenLayout:
	call CGB_FillBattleScreenAttrmap
	jp ApplyAttrmap

CGB_FillBattleScreenAttrmap:
	call InitPartyMenuBGPal7
	hlcoord 0, 0, wAttrmap
	ld bc, SCREEN_AREA
	ld a, PAL_BATTLE_BG_ENEMY_HP
	call ByteFill
	hlcoord 0, 4, wAttrmap
	lb bc, 8, 10
	ld a, PAL_BATTLE_BG_PLAYER
	call FillBoxCGB
	hlcoord 10, 0, wAttrmap
	lb bc, 7, 10
	ld a, PAL_BATTLE_BG_ENEMY
	call FillBoxCGB
	hlcoord 0, 0, wAttrmap
	lb bc, 4, 10
	ld a, PAL_BATTLE_BG_ENEMY_HP
	call FillBoxCGB
	hlcoord 10, 7, wAttrmap
	lb bc, 5, 10
	ld a, PAL_BATTLE_BG_PLAYER_HP
	call FillBoxCGB
	hlcoord 9, 11, wAttrmap
	lb bc, 1, 10
	ld a, PAL_BATTLE_BG_EXP
	call FillBoxCGB
	call CGB_BattleHPLabelAttrs
	hlcoord 0, 12, wAttrmap
	ld bc, 6 * SCREEN_WIDTH
	ld a, PAL_BATTLE_BG_TEXT
	call ByteFill
	call CGB_BattleStatusIconAttrs
	ld hl, BattleObjectPals
	ld de, wOBPals1 palette PAL_BATTLE_OB_GRAY
	ld bc, 6 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM
	ret

CGB_BattleHPLabelAttrs:
	hlcoord 2, 2, wAttrmap
	ld a, PAL_BATTLE_BG_EXP
	ld [hli], a
	ld [hl], a
	hlcoord 10, 9, wAttrmap
	ld [hli], a
	ld [hl], a
	ret

CGB_BattleStatusIconAttrs:
	ld a, [wBattleMonStatus]
	and ALL_STATUS
	jr z, .enemy
	hlcoord BATTLE_STATUS_ICON_PLAYER_X, BATTLE_STATUS_ICON_PLAYER_Y, wAttrmap
	ld a, BATTLE_STATUS_ICON_ATTR
	call CGB_SetStatusIconAttrs

.enemy
	ld a, [wEnemyMonStatus]
	and ALL_STATUS
	ret z
	hlcoord BATTLE_STATUS_ICON_ENEMY_X, BATTLE_STATUS_ICON_ENEMY_Y, wAttrmap
	ld a, BATTLE_STATUS_ICON_ATTR
	jp CGB_SetStatusIconAttrs

InitPartyMenuBGPal7:
	farcall Function100dc0
Mobile_InitPartyMenuBGPal7:
	ld hl, PartyMenuBGPalette
	jr nc, .not_mobile
	ld hl, PartyMenuBGMobilePalette
.not_mobile
	ld de, wBGPals1 palette 7
	ld bc, 1 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	ret

InitPartyMenuBGPal0:
	farcall Function100dc0
	ld hl, PartyMenuBGPalette
	jr nc, .not_mobile
	ld hl, PartyMenuBGMobilePalette
.not_mobile
	ld de, wBGPals1 palette 0
	ld bc, 1 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	ret

_CGB_PokegearPals:
	ld a, [wPlayerGender]
	bit PLAYERGENDER_FEMALE_F, a
	jr z, .male
	ld hl, FemalePokegearPals
	jr .got_pals

.male
	ld hl, MalePokegearPals
.got_pals
	ld de, wBGPals1
	ld bc, 6 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_StatsScreenHPPals:
	ld de, wBGPals1
	ld a, [wCurHPPal]
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	ld bc, HPBarPals
	add hl, bc
	call LoadPalette_White_Col1_Col2_Black ; hp palette
	ld a, [wCurPartySpecies]
	ld bc, wTempMonDVs
	call GetPlayerOrMonPalettePointer
	call LoadPalette_White_Col1_Col2_Black ; mon palette
	ld hl, ExpBarPalette
	call LoadPalette_White_Col1_Col2_Black ; exp palette
	ld hl, StatsScreenPagePals
	ld de, wBGPals1 palette 3
	ld bc, 2 palettes ; pink/green and blue page palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	call WipeAttrmap

	hlcoord 0, 0, wAttrmap
	lb bc, 8, SCREEN_WIDTH
	ld a, $1 ; mon palette
	call FillBoxCGB

	hlcoord 10, 16, wAttrmap
	ld bc, 10
	ld a, $2 ; exp palette
	call ByteFill

	hlcoord 13, 5, wAttrmap
	lb bc, 2, 2
	ld a, $3 ; pink page palette
	call FillBoxCGB

	hlcoord 15, 5, wAttrmap
	lb bc, 2, 2
	ld a, $3 ; pink/green page palette
	call FillBoxCGB

	hlcoord 17, 5, wAttrmap
	lb bc, 2, 2
	ld a, $4 ; blue page palette
	call FillBoxCGB

	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

StatsScreenPagePals:
INCLUDE "gfx/stats/pages.pal"

StatsScreenPals:
INCLUDE "gfx/stats/stats.pal"

_CGB_Pokedex:
	ld a, [wJumptableIndex]
	cp DEXSTATE_MAIN_SCR
	jp z, _CGB_PokedexList
	cp DEXSTATE_UPDATE_MAIN_SCR
	jp z, _CGB_PokedexList
	ld hl, PokedexUIPalette
	ld de, wBGPals1
	call LoadHLPaletteIntoDE ; dex interface palette
	ld a, [wCurPartySpecies]
	cp $ff
	jr nz, .is_pokemon
	ld hl, PokedexQuestionMarkPalette
	call LoadHLPaletteIntoDE ; green question mark palette
	jr .got_palette

.is_pokemon
	call GetMonPalettePointer
	call LoadPalette_White_Col1_Col2_Black ; mon palette
.got_palette
	call WipeAttrmap
	hlcoord 1, 1, wAttrmap
	lb bc, 7, 7
	ld a, $1 ; green question mark palette
	call FillBoxCGB
	ld a, [wJumptableIndex]
	cp DEXSTATE_DETAIL_ENTER
	jr c, .skip_footprint
	cp DEXSTATE_DETAIL_SWITCH + 1
	jr nc, .skip_footprint
	ld a, [wPokedexResidentFootprintSpecies]
	cp -1
	jr z, .skip_footprint
	hlcoord 18, 1, wAttrmap
	lb bc, 2, 2
	ld a, BG_BANK1
	call FillBoxCGB
.skip_footprint
	call InitPartyMenuOBPals
	ld hl, PokedexCursorPalette
	ld de, wOBPals1 palette 7 ; green cursor palette
	ld bc, 1 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

PokedexQuestionMarkPalette:
INCLUDE "gfx/pokedex/question_mark.pal"

PokedexCursorPalette:
INCLUDE "gfx/pokedex/cursor.pal"

_CGB_PokedexList:
	ld hl, PokedexUIPalette
	ld de, wBGPals1 palette 0
	call LoadHLPaletteIntoDE
	call CGB_PokedexLoadFrontpicPalette
	call CGB_PokedexLoadListIconPalettes

	ld hl, PokedexListCursorPalette
	ld de, wOBPals1 palette 0
	call LoadHLPaletteIntoDE
	ld hl, PokedexListCaughtBallPalette
	ld de, wOBPals1 palette 1
	call LoadHLPaletteIntoDE
	ld hl, PokedexListScrollThumbPalette
	ld de, wOBPals1 palette 5
	call LoadHLPaletteIntoDE

	call WipeAttrmap
	hlcoord 1, 1, wAttrmap
	lb bc, 7, 7
	ld a, [wCurPartySpecies]
	cp $ff
	ld a, 1
	jr nz, .got_frontpic_attr
	or BG_BANK1
.got_frontpic_attr
	call FillBoxCGB
	hlcoord 0, 8, wAttrmap
	lb bc, 1, 7
	ld a, BG_BANK1
	call FillBoxCGB
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

CGB_PokedexLoadListIconPalettes:
	ld a, [wPokedexGridIconPalettes + 0]
	ld de, wBGPals1 palette 2
	call .LoadBGIconPalette
	ld a, [wPokedexGridIconPalettes + 2]
	ld de, wBGPals1 palette 3
	call .LoadBGIconPalette
	ld a, [wPokedexGridIconPalettes + 3]
	ld de, wBGPals1 palette 4
	call .LoadBGIconPalette
	ld a, [wPokedexGridIconPalettes + 5]
	ld de, wBGPals1 palette 5
	call .LoadBGIconPalette
	ld a, [wPokedexGridIconPalettes + 6]
	ld de, wBGPals1 palette 6
	call .LoadBGIconPalette
	ld a, [wPokedexGridIconPalettes + 8]
	ld de, wBGPals1 palette 7
	call .LoadBGIconPalette
	ld a, [wPokedexGridIconPalettes + 1]
	ld de, wOBPals1 palette 2
	call .LoadIconPalette
	ld a, [wPokedexGridIconPalettes + 4]
	ld de, wOBPals1 palette 3
	call .LoadIconPalette
	ld a, [wPokedexGridIconPalettes + 7]
	ld de, wOBPals1 palette 4
	call .LoadIconPalette
	ret

.LoadBGIconPalette:
	push de
	call .LoadIconPalette
	pop de
	ld hl, PokedexListDarkGray
	ld bc, 1 colors
	ld a, BANK(wBGPals1)
	jp FarCopyWRAM

.LoadIconPalette:
; a = PartyMenuOBPals palette, de = destination palette
	and $f
	add a
	add a
	add a
	ld l, a
	ld h, 0
	ld bc, PartyMenuOBPals
	add hl, bc
	ld bc, 1 palettes
	ld a, BANK(wBGPals1)
	jp FarCopyWRAM

CGB_PokedexStageListPalettes::
; Build the complete selection-dependent palette state immediately before the
; scroll transaction copies it to hardware.
	call CGB_PokedexLoadFrontpicPalette
	call CGB_PokedexLoadListIconPalettes
	jp ApplyPals

CGB_PokedexPrepareFrontpicPalette::
; Stage the selected frontpic palette without making it visible yet.
	ldh a, [hCGB]
	and a
	ret z
	jp CGB_PokedexLoadFrontpicPalette

CGB_PokedexCommitFrontpicPalette::
; Copy only the staged frontpic palette into the active buffer and hardware.
; The caller schedules this after the old portrait's final visible scanline.
	ldh a, [hCGB]
	and a
	ret z
	ld hl, wBGPals1 palette 1
	ld de, wBGPals2 palette 1
	ld bc, 1 palettes
	ld a, BANK(wGBCPalettes)
	call FarCopyWRAM

	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals2)
	ldh [rWBK], a
	ld hl, wBGPals2 palette 1
	ld a, BGPI_AUTOINC palette 1
	ldh [rBGPI], a
	ld c, LOW(rBGPD)
	ld b, 1 palettes
.copy
.wait_palette
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_palette
	ld a, [hli]
	ldh [c], a
	dec b
	jr nz, .copy
	pop af
	ldh [rWBK], a
	ret

CGB_PokedexLoadFrontpicPalette:
	ld de, wBGPals1 palette 1
	ld a, [wCurPartySpecies]
	cp $ff
	jr nz, .pokemon_palette
	ld hl, PokedexQuestionMarkPalette
	jp LoadHLPaletteIntoDE

.pokemon_palette
	call GetMonPalettePointer
	jp LoadPalette_White_Col1_Col2_Black

PokedexUIPalette:
	RGB 31, 31, 31
	RGB 26, 10, 06
	RGB 05, 05, 05
	RGB 00, 00, 00

PokedexListCursorPalette:
	RGB 00, 00, 00
	RGB 11, 23, 00
	RGB 00, 00, 00
	RGB 00, 00, 00

PokedexListCaughtBallPalette:
	RGB 00, 00, 00
	RGB 31, 31, 31
	RGB 31, 20, 10
	RGB 31, 07, 01

PokedexListScrollThumbPalette:
	RGB 00, 00, 00
	RGB 27, 31, 27
	RGB 31, 07, 01
	RGB 00, 00, 00

PokedexListDarkGray:
	RGB 05, 05, 05

_CGB_BillsPC:
	ld de, wBGPals1
	ld a, PREDEFPAL_POKEDEX
	call GetPredefPal
	call LoadHLPaletteIntoDE
	ld a, [wCurPartySpecies]
	cp $ff
	jr nz, .GetMonPalette
	ld hl, BillsPCOrangePalette
	call LoadHLPaletteIntoDE
	jr .GotPalette

.GetMonPalette:
	ld bc, wTempMonDVs
	call GetPlayerOrMonPalettePointer
	call LoadPalette_White_Col1_Col2_Black
.GotPalette:
	call WipeAttrmap
	hlcoord 1, 4, wAttrmap
	lb bc, 7, 7
	ld a, $1 ; mon palette
	call FillBoxCGB
	call InitPartyMenuOBPals
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_Unknown: ; unreferenced
	ld hl, BillsPCOrangePalette
	call LoadHLPaletteIntoDE
	jr .GotPalette

.GetMonPalette: ; unreferenced
	ld bc, wTempMonDVs
	call GetPlayerOrMonPalettePointer
	call LoadPalette_White_Col1_Col2_Black
.GotPalette:
	call WipeAttrmap
	hlcoord 1, 1, wAttrmap
	lb bc, 7, 7
	ld a, $1 ; mon palette
	call FillBoxCGB
	call InitPartyMenuOBPals
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

BillsPCOrangePalette:
INCLUDE "gfx/pc/orange.pal"

_CGB_PokedexUnownMode:
	ld hl, PokedexUIPalette
	ld de, wBGPals1
	call LoadHLPaletteIntoDE
	ld a, [wCurPartySpecies]
	call GetMonPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	call WipeAttrmap
	hlcoord 7, 5, wAttrmap
	lb bc, 7, 7
	ld a, $1 ; mon palette
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 4, 3, wAttrmap
	lb bc, 1, 11
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 4, 4, wAttrmap
	lb bc, 8, 1
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 14, 4, wAttrmap
	lb bc, 7, 1
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 3, 2, wAttrmap
	lb bc, 1, 1
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 5, 2, wAttrmap
	lb bc, 1, 9
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 15, 2, wAttrmap
	lb bc, 1, 1
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 3, 4, wAttrmap
	lb bc, 8, 1
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 15, 4, wAttrmap
	lb bc, 7, 1
	call FillBoxCGB
	ld a, BG_BANK1
	hlcoord 4, 15, wAttrmap
	lb bc, 1, 12
	call FillBoxCGB
	call InitPartyMenuOBPals
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_SlotMachine:
	ld hl, SlotMachinePals
	ld de, wBGPals1
	ld bc, 16 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	call WipeAttrmap
	hlcoord 0, 2, wAttrmap
	lb bc, 10, 3
	ld a, $2 ; "3" palette
	call FillBoxCGB
	hlcoord 17, 2, wAttrmap
	lb bc, 10, 3
	ld a, $2 ; "3" palette
	call FillBoxCGB
	hlcoord 0, 4, wAttrmap
	lb bc, 6, 3
	ld a, $3 ; "2" palette
	call FillBoxCGB
	hlcoord 17, 4, wAttrmap
	lb bc, 6, 3
	ld a, $3 ; "2" palette
	call FillBoxCGB
	hlcoord 0, 6, wAttrmap
	lb bc, 2, 3
	ld a, $4 ; "1" palette
	call FillBoxCGB
	hlcoord 17, 6, wAttrmap
	lb bc, 2, 3
	ld a, $4 ; "1" palette
	call FillBoxCGB
	hlcoord 4, 2, wAttrmap
	lb bc, 2, 12
	ld a, $1 ; Vileplume palette
	call FillBoxCGB
	hlcoord 3, 2, wAttrmap
	lb bc, 10, 1
	ld a, $1 ; lights palette
	call FillBoxCGB
	hlcoord 16, 2, wAttrmap
	lb bc, 10, 1
	ld a, $1 ; lights palette
	call FillBoxCGB
	hlcoord 0, 12, wAttrmap
	ld bc, 6 * SCREEN_WIDTH
	ld a, $7 ; text palette
	call ByteFill
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_BetaTitleScreen:
	ld hl, PalPacket_BetaTitleScreen + 1
	call CopyFourPalettes
	call WipeAttrmap
	ld de, wOBPals1
	ld a, PREDEFPAL_PACK
	call GetPredefPal
	call LoadHLPaletteIntoDE
	hlcoord 0, 6, wAttrmap
	lb bc, 12, SCREEN_WIDTH
	ld a, $1
	call FillBoxCGB
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_GSIntro:
	ld b, 0
	ld hl, .Jumptable
	add hl, bc
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jp hl

.Jumptable:
	dw .ShellderLaprasScene
	dw .JigglypuffPikachuScene
	dw .StartersCharizardScene

.ShellderLaprasScene:
	ld hl, .ShellderLaprasBGPalette
	ld de, wBGPals1
	call LoadHLPaletteIntoDE
	ld hl, .ShellderLaprasOBPals
	ld de, wOBPals1
	ld bc, 2 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM
	call WipeAttrmap
	ret

.ShellderLaprasBGPalette:
INCLUDE "gfx/intro/gs_shellder_lapras_bg.pal"

.ShellderLaprasOBPals:
INCLUDE "gfx/intro/gs_shellder_lapras_ob.pal"

.JigglypuffPikachuScene:
	ld de, wBGPals1
	ld a, PREDEFPAL_GS_INTRO_JIGGLYPUFF_PIKACHU_BG
	call GetPredefPal
	call LoadHLPaletteIntoDE

	ld de, wOBPals1
	ld a, PREDEFPAL_GS_INTRO_JIGGLYPUFF_PIKACHU_OB
	call GetPredefPal
	call LoadHLPaletteIntoDE
	call WipeAttrmap
	ret

.StartersCharizardScene:
	ld hl, PalPacket_Pack + 1
	call CopyFourPalettes
	ld de, wOBPals1
	ld a, PREDEFPAL_GS_INTRO_STARTERS_TRANSITION
	call GetPredefPal
	call LoadHLPaletteIntoDE
	call WipeAttrmap
	ret

_CGB_BetaPoker:
	ld hl, BetaPokerPals
	ld de, wBGPals1
	ld bc, 5 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	call ApplyPals
	call WipeAttrmap
	call ApplyAttrmap
	ret

_CGB_Diploma:
	ld hl, DiplomaPalettes
	ld de, wBGPals1
	assert DiplomaPalettes + 8 palettes == PartyMenuOBPals
	ld bc, 16 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM

	ld hl, PalPacket_Diploma + 1
	call CopyFourPalettes
	call WipeAttrmap
	call ApplyAttrmap
	ret

_CGB_MapPals:
	call LoadMapPals
	ld a, SCGB_MAPPALS
	ld [wDefaultSGBLayout], a
	ret

_CGB_PartyMenu:
	ld hl, PalPacket_PartyMenu + 1
	call CopyFourPalettes
	call InitPartyMenuBGPal0
	call LoadPartyMenuStatusIconPalettes
	call InitPartyMenuBGPal7
	call InitPartyMenuOBPals
	call CGB_PartyMenuStatusIconAttrs
	call ApplyAttrmap
	ret

CGB_PartyMenuStatusIconAttrs:
	ld a, [wPartyCount]
	and a
	ret z
	ld c, a
	ld b, 0
	hlcoord 3, 2, wAttrmap

.loop
	push bc
	push hl
	call CGB_GetPartyStatusIcon
	jr nc, .no_icon
	call CGB_GetStatusIconAttr
	jr .got_attr

.no_icon
	xor a

.got_attr
	pop hl
	push hl
	call CGB_SetStatusIconAttrs
	pop hl
	ld de, 2 * SCREEN_WIDTH
	add hl, de
	pop bc
	inc b
	dec c
	jr nz, .loop
	ret

CGB_GetPartyStatusIcon:
; input:
;   b = party index
; output:
;   carry set and a = STATUS_ICON_* if status/fainted, carry clear otherwise
	ld d, b
	ld a, d
	ld bc, PARTYMON_STRUCT_LENGTH
	ld hl, wPartyMon1Species
	call AddNTimes
	ld a, [hl]
	cp EGG
	jr z, .no_icon

	ld a, d
	ld bc, PARTYMON_STRUCT_LENGTH
	ld hl, wPartyMon1HP
	call AddNTimes
	ld a, [hli]
	or [hl]
	jr nz, .check_status
	ld a, STATUS_ICON_FAINTED
	scf
	ret

.check_status
	ld a, d
	ld bc, PARTYMON_STRUCT_LENGTH
	ld hl, wPartyMon1Status
	call AddNTimes
	ld a, [hl]
	bit PSN, a
	jr nz, .poison
	bit BRN, a
	jr nz, .burn
	bit FRZ, a
	jr nz, .freeze
	bit PAR, a
	jr nz, .paralysis
	and SLP_MASK
	jr nz, .sleep

.no_icon
	and a
	ret

.poison
	ld a, [wBattleMode]
	and a
	jr z, .regular_poison
	ld a, [wCurBattleMon]
	cp d
	jr nz, .regular_poison
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_TOXIC, a
	jr z, .regular_poison
	ld a, STATUS_ICON_TOXIC
	scf
	ret

.regular_poison
	ld a, STATUS_ICON_POISON
	scf
	ret

.burn
	ld a, STATUS_ICON_BURN
	scf
	ret

.freeze
	ld a, STATUS_ICON_FREEZE
	scf
	ret

.paralysis
	ld a, STATUS_ICON_PARALYSIS
	scf
	ret

.sleep
	ld a, STATUS_ICON_SLEEP
	scf
	ret

CGB_GetStatusIconAttr:
; input:
;   a = STATUS_ICON_* constant
; output:
;   a = attr byte, using VRAM bank 1 and BG palettes 4-6
	cp STATUS_ICON_FREEZE
	jr c, .burn_fainted
	cp STATUS_ICON_POISON
	jr c, .freeze_paralysis
	ld a, $0e
	ret

.burn_fainted
	ld a, $0c
	ret

.freeze_paralysis
	ld a, $0d
	ret

CGB_SetStatusIconAttrs:
; input:
;   hl = attrmap destination
;   a  = attr byte
	ld c, STATUS_ICON_TILES
.loop
	ld [hli], a
	dec c
	jr nz, .loop
	ret

_CGB_Evolution:
	ld de, wBGPals1
	ld a, c
	and a
	jr z, .pokemon
	ld a, PREDEFPAL_BLACKOUT
	call GetPredefPal
	call LoadHLPaletteIntoDE
	jr .got_palette

.pokemon
	ld hl, wPartyMon1DVs
	ld bc, PARTYMON_STRUCT_LENGTH
	ld a, [wCurPartyMon]
	call AddNTimes
	ld c, l
	ld b, h
	ld a, [wPlayerHPPal]
	call GetPlayerOrMonPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld hl, BattleObjectPals
	ld de, wOBPals1 palette PAL_BATTLE_OB_GRAY
	ld bc, 6 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM

.got_palette
	call WipeAttrmap
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_GSTitleScreen:
	ld hl, UnusedGSTitleBGPals
	ld de, wBGPals1
	ld bc, 5 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	ld hl, UnusedGSTitleOBPals
	ld de, wOBPals1
	ld bc, 2 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM
	ld a, SCGB_DIPLOMA
	ld [wDefaultSGBLayout], a
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_Unused0D:
	ld hl, PalPacket_Diploma + 1
	call CopyFourPalettes
	call WipeAttrmap
	call ApplyAttrmap
	ret

_CGB_UnownPuzzle:
	ld hl, PalPacket_UnownPuzzle + 1
	call CopyFourPalettes
	ld de, wOBPals1
	ld a, PREDEFPAL_UNOWN_PUZZLE
	call GetPredefPal
	call LoadHLPaletteIntoDE
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld hl, wOBPals1
	ld a, LOW(palred 31 + palgreen 0 + palblue 0)
	ld [hli], a
	ld a, HIGH(palred 31 + palgreen 0 + palblue 0)
	ld [hl], a
	pop af
	ldh [rWBK], a
	call WipeAttrmap
	call ApplyAttrmap
	ret

_CGB_TrainerCard:
	ld de, wBGPals1
	xor a ; CHRIS
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, FALKNER ; KRIS
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, BUGSY
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, WHITNEY
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, MORTY
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, CHUCK
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, JASMINE
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, PRYCE
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld hl, .BadgePalettes
	ld de, wOBPals1
	ld bc, 8 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM

	; fill screen with opposite-gender palette for the card border
	hlcoord 0, 0, wAttrmap
	ld bc, SCREEN_AREA
	ld a, [wPlayerGender]
	and a
	ld a, $1 ; kris
	jr z, .got_gender
	ld a, $0 ; chris
.got_gender
	call ByteFill
	; fill trainer sprite area with same-gender palette
	hlcoord 14, 1, wAttrmap
	lb bc, 7, 5
	ld a, [wPlayerGender]
	and a
	ld a, $0 ; chris
	jr z, .got_gender2
	ld a, $1 ; kris
.got_gender2
	call FillBoxCGB
	; top-right corner still uses the border's palette
	hlcoord 18, 1, wAttrmap
	ld [hl], $1
	hlcoord 3, 10, wAttrmap
	lb bc, 3, 3
	ld a, $1 ; falkner
	call FillBoxCGB
	hlcoord 7, 10, wAttrmap
	lb bc, 3, 3
	ld a, $2 ; bugsy
	call FillBoxCGB
	hlcoord 11, 10, wAttrmap
	lb bc, 3, 3
	ld a, $3 ; whitney
	call FillBoxCGB
	hlcoord 15, 10, wAttrmap
	lb bc, 3, 3
	ld a, $4 ; morty
	call FillBoxCGB
	hlcoord 3, 13, wAttrmap
	lb bc, 3, 3
	ld a, $5 ; chuck
	call FillBoxCGB
	hlcoord 7, 13, wAttrmap
	lb bc, 3, 3
	ld a, $6 ; jasmine
	call FillBoxCGB
	hlcoord 11, 13, wAttrmap
	lb bc, 3, 3
	ld a, $7 ; pryce
	call FillBoxCGB
	; clair uses kris's palette
	ld a, [wPlayerGender]
	and a
	push af
	jr z, .got_gender3
	hlcoord 15, 13, wAttrmap
	lb bc, 3, 3
	ld a, $1
	call FillBoxCGB
.got_gender3
	pop af
	ld c, $0
	jr nz, .got_gender4
	inc c
.got_gender4
	ld a, c
	hlcoord 18, 1, wAttrmap
	ld [hl], a
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

.BadgePalettes:
INCLUDE "gfx/trainer_card/badges.pal"

_CGB_TrainerCardKanto:
	ld de, wBGPals1
	xor a ; CHRIS & MISTY
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, FALKNER ; KRIS
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, BROCK
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, LT_SURGE ; ERIKA
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, JANINE
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, SABRINA
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, BLAINE
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld a, BLUE
	call GetTrainerPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	ld hl, .BadgePalettes
	ld de, wOBPals1
	ld bc, 8 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM

	; fill screen with opposite-gender palette for the card border
	hlcoord 0, 0, wAttrmap
	ld bc, SCREEN_AREA
	ld a, [wPlayerGender]
	and a
	ld a, $1 ; kris
	jr z, .got_gender
	ld a, $0 ; chris
.got_gender
	call ByteFill
	; fill trainer sprite area with same-gender palette
	hlcoord 14, 1, wAttrmap
	lb bc, 7, 5
	ld a, [wPlayerGender]
	and a
	ld a, $0 ; chris
	jr z, .got_gender2
	ld a, $1 ; kris
.got_gender2
	call FillBoxCGB
	hlcoord 3, 10, wAttrmap
	lb bc, 3, 3
	ld a, $2 ; brock
	call FillBoxCGB
	hlcoord 7, 10, wAttrmap
	lb bc, 3, 3
	ld a, $0 ; misty / chris
	call FillBoxCGB
	hlcoord 11, 10, wAttrmap
	lb bc, 3, 3
	ld a, $3 ; lt.surge / erika
	call FillBoxCGB
	hlcoord 15, 10, wAttrmap
	lb bc, 3, 3
	ld a, $3 ; erika / lt.surge
	call FillBoxCGB
	hlcoord 3, 13, wAttrmap
	lb bc, 3, 3
	ld a, $4 ; janine
	call FillBoxCGB
	hlcoord 7, 13, wAttrmap
	lb bc, 3, 3
	ld a, $5 ; sabrina
	call FillBoxCGB
	hlcoord 11, 13, wAttrmap
	lb bc, 3, 3
	ld a, $6 ; blaine
	call FillBoxCGB
	hlcoord 15, 13, wAttrmap
	lb bc, 3, 3
	ld a, $7 ; blue
	call FillBoxCGB
	; top-right corner still uses the border's palette
	ld a, [wPlayerGender]
	and a
	ld a, $1 ; kris
	jr z, .got_gender3
	ld a, $0 ; chris
.got_gender3
	hlcoord 18, 1, wAttrmap
	ld [hl], a
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

.BadgePalettes:
INCLUDE "gfx/trainer_card/kanto_badges.pal"

_CGB_MoveList:
	ld de, wBGPals1
	ld a, PREDEFPAL_GOLDENROD
	call GetPredefPal
	call LoadHLPaletteIntoDE
	ld a, [wPlayerHPPal]
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	ld bc, HPBarPals
	add hl, bc
	call LoadPalette_White_Col1_Col2_Black
	call WipeAttrmap
	hlcoord 11, 1, wAttrmap
	lb bc, 2, 9
	ld a, $1
	call FillBoxCGB
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_BetaPikachuMinigame:
	ld hl, PalPacket_BetaPikachuMinigame + 1
	call CopyFourPalettes
	call WipeAttrmap
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_PokedexSearchOption:
	ld hl, PokedexUIPalette
	ld de, wBGPals1
	call LoadHLPaletteIntoDE
	call WipeAttrmap
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_PackPals:
; pack pals
	ld a, [wBattleType]
	cp BATTLETYPE_TUTORIAL
	jr z, .tutorial_male

	ld a, [wPlayerGender]
	bit PLAYERGENDER_FEMALE_F, a
	jr z, .tutorial_male

	ld hl, .KrisPackPals
	jr .got_gender

.tutorial_male
	ld hl, .ChrisPackPals

.got_gender
	ld de, wBGPals1
	ld bc, 8 palettes
	ld a, BANK(wBGPals1)
	call FarCopyWRAM
	call WipeAttrmap
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

.ChrisPackPals:
INCLUDE "gfx/pack/pack.pal"

.KrisPackPals:
INCLUDE "gfx/pack/pack_f.pal"

_CGB_Pokepic:
	call _CGB_MapPals
	ld de, SCREEN_WIDTH
	hlcoord 0, 0, wAttrmap
	ld a, [wMenuBorderTopCoord]
.loop
	and a
	jr z, .found_top
	dec a
	add hl, de
	jr .loop

.found_top
	ld a, [wMenuBorderLeftCoord]
	ld e, a
	ld d, 0
	add hl, de
	ld a, [wMenuBorderTopCoord]
	ld b, a
	ld a, [wMenuBorderBottomCoord]
	inc a
	sub b
	ld b, a
	ld a, [wMenuBorderLeftCoord]
	ld c, a
	ld a, [wMenuBorderRightCoord]
	sub c
	inc a
	ld c, a
	ld a, PAL_BG_GRAY
	call FillBoxCGB
	call ApplyAttrmap
	ret

_CGB_MagnetTrain: ; unused
	ld hl, PalPacket_MagnetTrain + 1
	call CopyFourPalettes
	call WipeAttrmap
	hlcoord 0, 4, wAttrmap
	lb bc, 10, SCREEN_WIDTH
	ld a, PAL_BG_GREEN
	call FillBoxCGB
	hlcoord 0, 6, wAttrmap
	lb bc, 6, SCREEN_WIDTH
	ld a, PAL_BG_RED
	call FillBoxCGB
	call ApplyAttrmap
	call ApplyPals
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ret

_CGB_GamefreakLogo:
	ld de, wBGPals1
	ld a, PREDEFPAL_GAMEFREAK_LOGO_BG
	call GetPredefPal
	call LoadHLPaletteIntoDE
	ld hl, .GamefreakDittoPalette
	ld de, wOBPals1
	call LoadHLPaletteIntoDE
	ld hl, .GamefreakDittoPalette
	ld de, wOBPals1 palette 1
	call LoadHLPaletteIntoDE
	call WipeAttrmap
	call ApplyAttrmap
	call ApplyPals
	ret

.GamefreakDittoPalette:
INCLUDE "gfx/splash/ditto.pal"

_CGB_PlayerOrMonFrontpicPals:
	ld de, wBGPals1
	ld a, [wCurPartySpecies]
	ld bc, wTempMonDVs
	call GetPlayerOrMonPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	call WipeAttrmap
	call ApplyAttrmap
	call ApplyPals
	ret

_CGB_Unused1E:
	ld de, wBGPals1
	ld a, [wCurPartySpecies]
	call GetMonPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	call WipeAttrmap
	call ApplyAttrmap
	ret

_CGB_TradeTube:
	ld hl, PalPacket_TradeTube + 1
	call CopyFourPalettes
	ld hl, PartyMenuOBPals
	ld de, wOBPals1
	ld bc, 1 palettes
	ld a, BANK(wOBPals1)
	call FarCopyWRAM
	ld de, wOBPals1 palette 7
	ld a, PREDEFPAL_TRADE_TUBE
	call GetPredefPal
	call LoadHLPaletteIntoDE
	call WipeAttrmap
	ret

_CGB_TrainerOrMonFrontpicPals:
	ld de, wBGPals1
	ld a, [wCurPartySpecies]
	ld bc, wTempMonDVs
	call GetFrontpicPalettePointer
	call LoadPalette_White_Col1_Col2_Black
	call WipeAttrmap
	call ApplyAttrmap
	call ApplyPals
	ret
