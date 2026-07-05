DEF ICON_4X2_TILES EQU 8
DEF ICON_COMPACT_TYPE_TILES EQU 4
DEF ICON_COMPACT_CATEGORY_TILES EQU 2
DEF ICON_PADDED_COMPACT_CATEGORY_TILES EQU 4

DEF ICON_MOVE_TYPE_TILE     EQU $68 ; uses $68-$6f
DEF ICON_MOVE_CATEGORY_TILE EQU $70 ; uses $70-$77

DEF ICON_BATTLE_MOVE_INFO_POWER_TILE         EQU $c0 ; uses $c0-$c1 in VRAM bank 0
DEF ICON_BATTLE_MOVE_INFO_ACCURACY_TILE      EQU ICON_BATTLE_MOVE_INFO_POWER_TILE + 2 ; uses $c2-$c3 in VRAM bank 0
DEF ICON_BATTLE_MOVE_INFO_EFFECT_CHANCE_TILE EQU ICON_BATTLE_MOVE_INFO_ACCURACY_TILE + 2 ; uses $c4-$c5 in VRAM bank 0
DEF ICON_BATTLE_MOVE_INFO_POWER_DEST_TILE    EQU ICON_BATTLE_MOVE_INFO_POWER_TILE - $80
DEF ICON_BATTLE_MOVE_INFO_ACCURACY_DEST_TILE EQU ICON_BATTLE_MOVE_INFO_ACCURACY_TILE - $80
DEF ICON_BATTLE_MOVE_INFO_EFFECT_CHANCE_DEST_TILE EQU ICON_BATTLE_MOVE_INFO_EFFECT_CHANCE_TILE - $80
DEF ICON_BATTLE_MOVE_INFO_TYPE_TILE          EQU $c6 ; uses $c6-$c9 in VRAM bank 0
DEF ICON_BATTLE_MOVE_INFO_TYPE_DEST_TILE     EQU ICON_BATTLE_MOVE_INFO_TYPE_TILE - $80
DEF ICON_BATTLE_MOVE_INFO_CATEGORY_TILE      EQU $ca ; uses $ca-$cd in VRAM bank 0
DEF ICON_BATTLE_MOVE_INFO_CATEGORY_DEST_TILE EQU ICON_BATTLE_MOVE_INFO_CATEGORY_TILE - $80

DEF ICON_MOVE_MENU_TYPE_X     EQU 11
DEF ICON_MOVE_MENU_CATEGORY_X EQU 15
DEF ICON_MOVE_MENU_Y          EQU 12

MoveCategoryIconGFXPointers::
	table_width 3
	dba PhysicalMoveCategoryIconGFX
	dba SpecialMoveCategoryIconGFX
	dba StatusMoveCategoryIconGFX
	assert_table_length NUM_MOVE_CATEGORIES

CompactMoveCategoryIconGFXPointers:
	table_width 3
	dba CompactPhysicalMoveCategoryIconGFX
	dba CompactSpecialMoveCategoryIconGFX
	dba CompactStatusMoveCategoryIconGFX
	assert_table_length NUM_MOVE_CATEGORIES

PaddedCompactMoveCategoryIconGFXPointers:
	table_width 3
	dba PaddedCompactPhysicalMoveCategoryIconGFX
	dba PaddedCompactSpecialMoveCategoryIconGFX
	dba PaddedCompactStatusMoveCategoryIconGFX
	assert_table_length NUM_MOVE_CATEGORIES

StatsStatusIconGFXPointers::
	table_width 3
	dba StatsBurnStatusIconGFX
	dba StatsFaintedStatusIconGFX
	dba StatsFreezeStatusIconGFX
	dba StatsParalysisStatusIconGFX
	dba StatsPoisonStatusIconGFX
	dba StatsSleepStatusIconGFX
	dba StatsToxicStatusIconGFX
	assert_table_length NUM_STATUS_ICONS

BattlePlayerStatusIconGFXPointers:
	table_width 3
	dba BurnStatusIconGFX
	dba BurnStatusIconGFX ; fainted is not shown in battle
	dba FreezeStatusIconGFX
	dba BattleParalysisStatusIconSlot1GFX
	dba PoisonStatusIconGFX
	dba BattleSleepStatusIconSlot1GFX
	dba ToxicStatusIconGFX
	assert_table_length NUM_STATUS_ICONS

BattleEnemyStatusIconGFXPointers:
	table_width 3
	dba BattleBurnStatusIconSlot2GFX
	dba BattleBurnStatusIconSlot2GFX ; fainted is not shown in battle
	dba BattleFreezeStatusIconSlot2GFX
	dba ParalysisStatusIconGFX
	dba BattlePoisonStatusIconSlot2GFX
	dba SleepStatusIconGFX
	dba BattleToxicStatusIconSlot2GFX
	assert_table_length NUM_STATUS_ICONS

TypeIconGFXPointers:
	; Physical block
	dba NormalTypeIconGFX      ; NORMAL       = 0
	dba FightingTypeIconGFX    ; FIGHTING     = 1
	dba FlyingTypeIconGFX      ; FLYING       = 2
	dba PoisonTypeIconGFX      ; POISON       = 3
	dba GroundTypeIconGFX      ; GROUND       = 4
	dba RockTypeIconGFX        ; ROCK         = 5
	dba NormalTypeIconGFX      ; BIRD         = 6 ; unused/fallback
	dba BugTypeIconGFX         ; BUG          = 7
	dba DarkTypeIconGFX        ; DARK         = 8
	dba SteelTypeIconGFX       ; STEEL        = 9

	; Unused type slots 10-18
	dba NormalTypeIconGFX      ; unused 10
	dba NormalTypeIconGFX      ; unused 11
	dba NormalTypeIconGFX      ; unused 12
	dba NormalTypeIconGFX      ; unused 13
	dba NormalTypeIconGFX      ; unused 14
	dba NormalTypeIconGFX      ; unused 15
	dba NormalTypeIconGFX      ; unused 16
	dba NormalTypeIconGFX      ; unused 17
	dba NormalTypeIconGFX      ; unused 18

	dba GhostTypeIconGFX       ; CURSE_TYPE   = 19 ; fallback

	; Special block
	dba FireTypeIconGFX        ; FIRE         = 20
	dba WaterTypeIconGFX       ; WATER        = 21
	dba GrassTypeIconGFX       ; GRASS        = 22
	dba ElectricTypeIconGFX    ; ELECTRIC     = 23
	dba PsychicTypeIconGFX     ; PSYCHIC_TYPE = 24
	dba IceTypeIconGFX         ; ICE          = 25
	dba DragonTypeIconGFX      ; DRAGON       = 26
	dba GhostTypeIconGFX       ; GHOST        = 27
	dba FairyTypeIconGFX       ; FAIRY        = 28
.end
	ASSERT .end - TypeIconGFXPointers == TYPES_END * 3

CompactTypeIconGFXPointers:
	; Physical block
	dba CompactNormalTypeIconGFX      ; NORMAL       = 0
	dba CompactFightingTypeIconGFX    ; FIGHTING     = 1
	dba CompactFlyingTypeIconGFX      ; FLYING       = 2
	dba CompactPoisonTypeIconGFX      ; POISON       = 3
	dba CompactGroundTypeIconGFX      ; GROUND       = 4
	dba CompactRockTypeIconGFX        ; ROCK         = 5
	dba CompactNormalTypeIconGFX      ; BIRD         = 6 ; unused/fallback
	dba CompactBugTypeIconGFX         ; BUG          = 7
	dba CompactDarkTypeIconGFX        ; DARK         = 8
	dba CompactSteelTypeIconGFX       ; STEEL        = 9

	; Unused type slots 10-18
	dba CompactNormalTypeIconGFX      ; unused 10
	dba CompactNormalTypeIconGFX      ; unused 11
	dba CompactNormalTypeIconGFX      ; unused 12
	dba CompactNormalTypeIconGFX      ; unused 13
	dba CompactNormalTypeIconGFX      ; unused 14
	dba CompactNormalTypeIconGFX      ; unused 15
	dba CompactNormalTypeIconGFX      ; unused 16
	dba CompactNormalTypeIconGFX      ; unused 17
	dba CompactNormalTypeIconGFX      ; unused 18

	dba CompactGhostTypeIconGFX       ; CURSE_TYPE   = 19 ; fallback

	; Special block
	dba CompactFireTypeIconGFX        ; FIRE         = 20
	dba CompactWaterTypeIconGFX       ; WATER        = 21
	dba CompactGrassTypeIconGFX       ; GRASS        = 22
	dba CompactElectricTypeIconGFX    ; ELECTRIC     = 23
	dba CompactPsychicTypeIconGFX     ; PSYCHIC_TYPE = 24
	dba CompactIceTypeIconGFX         ; ICE          = 25
	dba CompactDragonTypeIconGFX      ; DRAGON       = 26
	dba CompactGhostTypeIconGFX       ; GHOST        = 27
	dba CompactFairyTypeIconGFX       ; FAIRY        = 28
.end
	ASSERT .end - CompactTypeIconGFXPointers == TYPES_END * 3

Icon_LoadTypeIconGFX::
; Load one type icon into VRAM bank 1.
; input:
;   a  = type constant
;   hl = destination tile address, e.g. vTiles2 tile ICON_MOVE_TYPE_TILE
	push hl

	; de = a * 3, because TypeIconGFXPointers entries are dba: bank + word
	ld e, a
	ld d, 0
	ld hl, TypeIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	; b = bank, de = pointer
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	ld a, $1
	ldh [rVBK], a

	ld c, ICON_4X2_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

StatsScreen_LoadTypeIconGFX::
; Load one stats-page type icon into VRAM bank 0.
; input:
;   a  = type constant
;   hl = destination tile address, e.g. vTiles1 tile TYPE_ICON_SLOT_1_DEST_TILE
	push hl

	; de = a * 3, because TypeIconGFXPointers entries are dba: bank + word
	ld e, a
	ld d, 0
	ld hl, TypeIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	; b = bank, de = pointer
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld c, ICON_4X2_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

Icon_LoadCurrentMoveTypeIconGFX_Bank1::
StatsScreen_LoadCurrentMoveTypeIconGFX_Bank1::
; Load selected move's type icon graphics into VRAM bank 1.
; Uses wCurSpecies as selected move ID, matching the move menu convention.
; Destination:
;   vTiles2 tile $68-$6f, VRAM bank 1
	ld a, [wCurSpecies]
	ld l, a
	ld a, MOVE_TYPE
	call GetMoveAttribute

	ld hl, vTiles2 tile ICON_MOVE_TYPE_TILE
	jp Icon_LoadTypeIconGFX

Icon_LoadCurrentMoveCategoryIconGFX_Bank1::
	call Icon_GetCurrentMoveCategory
	ld hl, vTiles2 tile ICON_MOVE_CATEGORY_TILE
	jp Icon_LoadMoveCategoryIconGFX

Icon_LoadMoveCategoryIconGFX::
; Load one move category icon into VRAM bank 1.
; input:
;   a  = MOVE_CATEGORY_* constant
;   hl = destination tile address
	push hl

	; de = a * 3, because MoveCategoryIconGFXPointers entries are dba: bank + word
	ld e, a
	ld d, 0
	ld hl, MoveCategoryIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	; b = bank, de = source pointer
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	ld a, $1
	ldh [rVBK], a

	ld c, ICON_4X2_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

Icon_LoadCompactTypeIconGFX_Bank1:
; Load one compact type icon into VRAM bank 1.
; input:
;   a  = type constant
;   hl = destination tile address
	push hl

	ld e, a
	ld d, 0
	ld hl, CompactTypeIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	ld a, $1
	ldh [rVBK], a

	ld c, ICON_COMPACT_TYPE_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

Icon_LoadCompactTypeIconGFX_Bank0:
; Load one compact type icon into VRAM bank 0.
; input:
;   a  = type constant
;   hl = destination tile address
	push hl

	ld e, a
	ld d, 0
	ld hl, CompactTypeIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld c, ICON_COMPACT_TYPE_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

Icon_LoadCompactMoveCategoryIconGFX_Bank0:
; Load one compact category icon into VRAM bank 0 for OAM.
; input:
;   a  = MOVE_CATEGORY_* constant
;   hl = destination tile address
	push hl

	ld e, a
	ld d, 0
	ld hl, CompactMoveCategoryIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld c, ICON_COMPACT_CATEGORY_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

Icon_LoadPaddedCompactMoveCategoryIconGFX_Bank0:
; Load one padded compact category icon into VRAM bank 0 for BG use.
; input:
;   a  = MOVE_CATEGORY_* constant
;   hl = destination tile address
	push hl

	ld e, a
	ld d, 0
	ld hl, PaddedCompactMoveCategoryIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld c, ICON_PADDED_COMPACT_CATEGORY_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

Icon_LoadStatsStatusIconGFX::
; Load one stats-page status icon into VRAM bank 0.
; input:
;   a  = STATUS_ICON_* constant
;   hl = destination tile address
	push hl

	ld e, a
	ld d, 0
	ld hl, StatsStatusIconGFXPointers
	add hl, de
	add hl, de
	add hl, de

	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld c, STATUS_ICON_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

Icon_LoadBattlePlayerStatusIconGFX:
	ld de, BattlePlayerStatusIconGFXPointers
	jr Icon_LoadBattleStatusIconGFX

Icon_LoadBattleEnemyStatusIconGFX:
	ld de, BattleEnemyStatusIconGFXPointers

Icon_LoadBattleStatusIconGFX:
; Load one battle status icon into VRAM bank 0.
; input:
;   a  = STATUS_ICON_* constant
;   hl = destination tile address
;   de = battle status GFX pointer table
	push hl

	ld c, a
	ld b, 0
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
	add hl, de

	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	pop hl

	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld c, STATUS_ICON_TILES
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

BattleStatus_GetPlayerIcon:
	ld a, [wBattleMonStatus]
	ld hl, wPlayerSubStatus5
	jr BattleStatus_GetIcon

BattleStatus_GetEnemyIcon:
	ld a, [wEnemyMonStatus]
	ld hl, wEnemySubStatus5

BattleStatus_GetIcon:
	ld b, a
	bit PSN, b
	jr nz, .poison
	bit BRN, b
	jr nz, .burn
	bit FRZ, b
	jr nz, .freeze
	bit PAR, b
	jr nz, .paralysis
	ld a, b
	and SLP_MASK
	jr nz, .sleep

	and a
	ret

.poison
	ld a, [hl]
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

BattleStatus_LoadIconPalette:
	call BattleStatus_GetPlayerIcon
	jr nc, .no_player
	ld d, a
	jr .enemy

.no_player
	ld d, STATUS_ICON_NONE

.enemy
	call BattleStatus_GetEnemyIcon
	jr nc, .no_enemy
	ld c, a
	jr .load

.no_enemy
	ld c, STATUS_ICON_NONE

.load
	ld b, d
	farcall LoadBattleStatusIconPalette
	ret

BattleStatus_LoadHUDIconGFX::
; Farcall-safe. Refresh status icon graphics used by the battle HUD.
	ldh a, [hCGB]
	and a
	ret z

	call BattleStatus_GetPlayerIcon
	jr nc, .enemy
	push af
	ld hl, vTiles1 tile BATTLE_STATUS_ICON_PLAYER_DEST_TILE
	pop af
	call Icon_LoadBattlePlayerStatusIconGFX

.enemy
	call BattleStatus_GetEnemyIcon
	ret nc
	push af
	ld hl, vTiles1 tile BATTLE_STATUS_ICON_ENEMY_DEST_TILE
	pop af
	jp Icon_LoadBattleEnemyStatusIconGFX

BattleStatus_DrawPlayerHUDIcon::
; Farcall-safe. Draw the player's active battle status icon on CGB.
; Returns carry if an icon was drawn.
	ldh a, [hCGB]
	and a
	ret z

	call BattleStatus_LoadIconPalette
	call BattleStatus_GetPlayerIcon
	jr nc, .no_icon

	push af
	ld hl, vTiles1 tile BATTLE_STATUS_ICON_PLAYER_DEST_TILE
	pop af
	call Icon_LoadBattlePlayerStatusIconGFX

	hlcoord BATTLE_STATUS_ICON_PLAYER_X, BATTLE_STATUS_ICON_PLAYER_Y
	ld a, BATTLE_STATUS_ICON_PLAYER_TILE
	call Icon_Draw3x1

	hlcoord BATTLE_STATUS_ICON_PLAYER_X, BATTLE_STATUS_ICON_PLAYER_Y, wAttrmap
	ld a, BATTLE_STATUS_ICON_ATTR
	call Icon_Set3x1Attrs
	scf
	ret

.no_icon
	hlcoord BATTLE_STATUS_ICON_PLAYER_X, BATTLE_STATUS_ICON_PLAYER_Y, wAttrmap
	ld a, PAL_BATTLE_BG_PLAYER_HP
	call Icon_Set3x1Attrs
	and a
	ret

BattleStatus_DrawEnemyHUDIcon::
; Farcall-safe. Draw the enemy's active battle status icon on CGB.
; Returns carry if an icon was drawn.
	ldh a, [hCGB]
	and a
	ret z

	call BattleStatus_LoadIconPalette
	call BattleStatus_GetEnemyIcon
	jr nc, .no_icon

	push af
	ld hl, vTiles1 tile BATTLE_STATUS_ICON_ENEMY_DEST_TILE
	pop af
	call Icon_LoadBattleEnemyStatusIconGFX

	hlcoord BATTLE_STATUS_ICON_ENEMY_X, BATTLE_STATUS_ICON_ENEMY_Y
	ld a, BATTLE_STATUS_ICON_ENEMY_TILE
	call Icon_Draw3x1

	hlcoord BATTLE_STATUS_ICON_ENEMY_X, BATTLE_STATUS_ICON_ENEMY_Y, wAttrmap
	ld a, BATTLE_STATUS_ICON_ATTR
	call Icon_Set3x1Attrs
	scf
	ret

.no_icon
	hlcoord BATTLE_STATUS_ICON_ENEMY_X, BATTLE_STATUS_ICON_ENEMY_Y, wAttrmap
	ld a, PAL_BATTLE_BG_ENEMY_HP
	call Icon_Set3x1Attrs
	and a
	ret

Icon_LoadCurrentMoveIconsGFX_Bank1::
; Farcall-safe. Loads selected move type and category graphics to the shared
; move icon slots in VRAM bank 1.
	call Icon_LoadCurrentMoveTypeIconGFX_Bank1
	jp Icon_LoadCurrentMoveCategoryIconGFX_Bank1

Icon_LoadBattleMoveInfoTypeIconGFX_Bank0::
; Load the battle move-info type icon graphics into VRAM bank 0.
; Uses wPlayerMoveStruct, which UpdateMoveData fills immediately before the
; battle move-info panel is drawn.
	ld a, [wPlayerMoveStruct + MOVE_TYPE]
	ld hl, vTiles1 tile ICON_BATTLE_MOVE_INFO_TYPE_DEST_TILE
	jp Icon_LoadCompactTypeIconGFX_Bank0

Icon_LoadBattleMoveInfoCategoryIconGFX_Bank0:
	call Icon_GetBattleMoveInfoCategory
	ld hl, vTiles1 tile ICON_BATTLE_MOVE_INFO_CATEGORY_DEST_TILE
	jp Icon_LoadPaddedCompactMoveCategoryIconGFX_Bank0

Icon_LoadBattleMoveInfoStatIconGFX_Bank0:
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld de, MoveInfoPowerIconGFX
	ld hl, vTiles1 tile ICON_BATTLE_MOVE_INFO_POWER_DEST_TILE
	lb bc, BANK(MoveInfoPowerIconGFX), 2
	call Get2bpp

	ld de, MoveInfoAccuracyIconGFX
	ld hl, vTiles1 tile ICON_BATTLE_MOVE_INFO_ACCURACY_DEST_TILE
	lb bc, BANK(MoveInfoAccuracyIconGFX), 2
	call Get2bpp

	ld de, MoveInfoEffectChanceIconGFX
	ld hl, vTiles1 tile ICON_BATTLE_MOVE_INFO_EFFECT_CHANCE_DEST_TILE
	lb bc, BANK(MoveInfoEffectChanceIconGFX), 2
	call Get2bpp

	pop af
	ldh [rVBK], a
	ret

Icon_LoadBattleMoveInfoIconsGFX::
; Farcall-safe. Loads battle move-info graphics to their shared VRAM slots.
	call Icon_LoadBattleMoveInfoStatIconGFX_Bank0
	call Icon_LoadBattleMoveInfoTypeIconGFX_Bank0
	jp Icon_LoadBattleMoveInfoCategoryIconGFX_Bank0

Icon_GetCurrentMoveCategory::
; Return selected move's category in a.
; Uses wCurSpecies as selected move ID.
	ld a, [wCurSpecies]
	ld l, a
	ld a, MOVE_POWER
	call GetMoveAttribute
	cp 2
	jr c, .status

	ld a, [wCurSpecies]
	ld l, a
	ld a, MOVE_TYPE
	call GetMoveAttribute
	cp SPECIAL
	jr nc, .special

.physical
	ld a, MOVE_CATEGORY_PHYSICAL
	ret

.special
	ld a, MOVE_CATEGORY_SPECIAL
	ret

.status
	ld a, MOVE_CATEGORY_STATUS
	ret

Icon_GetBattleMoveInfoCategory::
; Return the battle move-info move's category in a.
; Uses wPlayerMoveStruct instead of wCurSpecies, since wCurSpecies is shared
; scratch state and the icon GFX loads can wait across frames.
	ld a, [wPlayerMoveStruct + MOVE_POWER]
	cp 2
	jr c, .status

	ld a, [wPlayerMoveStruct + MOVE_TYPE]
	cp SPECIAL
	jr nc, .special

.physical
	ld a, MOVE_CATEGORY_PHYSICAL
	ret

.special
	ld a, MOVE_CATEGORY_SPECIAL
	ret

.status
	ld a, MOVE_CATEGORY_STATUS
	ret

Icon_Draw4x2::
; input:
;   hl = tilemap destination
;   a  = starting tile ID
	ld c, 4
.top
	ld [hli], a
	inc a
	dec c
	jr nz, .top

	ld de, SCREEN_WIDTH - 4
	add hl, de

	ld c, 4
.bottom
	ld [hli], a
	inc a
	dec c
	jr nz, .bottom
	ret

Icon_Set4x2Attrs::
; input:
;   hl = attrmap destination
;   a  = attr byte
	push bc
	push de

	ld c, 4
.top
	ld [hli], a
	dec c
	jr nz, .top

	ld de, SCREEN_WIDTH - 4
	add hl, de

	ld c, 4
.bottom
	ld [hli], a
	dec c
	jr nz, .bottom

	pop de
	pop bc
	ret

Icon_Draw3x1::
; input:
;   hl = tilemap destination
;   a  = starting tile ID
	ld c, 3
.loop
	ld [hli], a
	inc a
	dec c
	jr nz, .loop
	ret

Icon_Set3x1Attrs::
; input:
;   hl = attrmap destination
;   a  = attr byte
	ld c, 3
.loop
	ld [hli], a
	dec c
	jr nz, .loop
	ret

Icon_Draw2x1:
; input:
;   hl = tilemap destination
;   a  = starting tile ID
	ld [hli], a
	inc a
	ld [hl], a
	ret

Icon_Set2x1Attrs:
; input:
;   hl = attrmap destination
;   a  = attr byte
	ld [hli], a
	ld [hl], a
	ret

Icon_Draw2x2:
; input:
;   hl = tilemap destination
;   a  = starting tile ID
	ld [hli], a
	inc a
	ld [hl], a
	inc a
	ld de, SCREEN_WIDTH - 1
	add hl, de
	ld [hli], a
	inc a
	ld [hl], a
	ret

Icon_Set2x2Attrs:
; input:
;   hl = attrmap destination
;   a  = attr byte
	ld [hli], a
	ld [hl], a
	ld de, SCREEN_WIDTH - 1
	add hl, de
	ld [hli], a
	ld [hl], a
	ret

Icon_Draw4x1:
; input:
;   hl = tilemap destination
;   a  = starting tile ID
	ld c, 4
.loop
	ld [hli], a
	inc a
	dec c
	jr nz, .loop
	ret

Icon_Set4x1Attrs:
; input:
;   hl = attrmap destination
;   a  = attr byte
	ld c, 4
.loop
	ld [hli], a
	dec c
	jr nz, .loop
	ret

BattleMoveInfo_LoadAndDrawIcons::
; Farcall-safe. Loads and draws the battle move-info type/category icons.
	call Icon_LoadBattleMoveInfoIconsGFX
	farcall LoadBattleMoveInfoIconPalettes

	hlcoord BATTLE_MOVE_INFO_STAT_ICON_X, BATTLE_MOVE_INFO_POWER_ICON_Y
	ld a, ICON_BATTLE_MOVE_INFO_POWER_TILE
	call Icon_Draw2x1

	hlcoord BATTLE_MOVE_INFO_STAT_ICON_X, BATTLE_MOVE_INFO_ACCURACY_ICON_Y
	ld a, ICON_BATTLE_MOVE_INFO_ACCURACY_TILE
	call Icon_Draw2x1

	hlcoord BATTLE_MOVE_INFO_STAT_ICON_X, BATTLE_MOVE_INFO_EFFECT_CHANCE_ICON_Y
	ld a, ICON_BATTLE_MOVE_INFO_EFFECT_CHANCE_TILE
	call Icon_Draw2x1

	hlcoord BATTLE_MOVE_INFO_TYPE_ICON_X, BATTLE_MOVE_INFO_TYPE_ICON_Y
	ld a, ICON_BATTLE_MOVE_INFO_TYPE_TILE
	call Icon_Draw4x1

	hlcoord BATTLE_MOVE_INFO_CATEGORY_ICON_X, BATTLE_MOVE_INFO_CATEGORY_ICON_Y
	ld a, ICON_BATTLE_MOVE_INFO_CATEGORY_TILE
	call Icon_Draw2x2

	hlcoord BATTLE_MOVE_INFO_STAT_ICON_X, BATTLE_MOVE_INFO_POWER_ICON_Y, wAttrmap
	ld a, BATTLE_MOVE_INFO_STAT_ICON_ATTR
	call Icon_Set2x1Attrs

	hlcoord BATTLE_MOVE_INFO_STAT_ICON_X, BATTLE_MOVE_INFO_ACCURACY_ICON_Y, wAttrmap
	ld a, BATTLE_MOVE_INFO_STAT_ICON_ATTR
	call Icon_Set2x1Attrs

	hlcoord BATTLE_MOVE_INFO_STAT_ICON_X, BATTLE_MOVE_INFO_EFFECT_CHANCE_ICON_Y, wAttrmap
	ld a, BATTLE_MOVE_INFO_STAT_ICON_ATTR
	call Icon_Set2x1Attrs

	hlcoord BATTLE_MOVE_INFO_TYPE_ICON_X, BATTLE_MOVE_INFO_TYPE_ICON_Y, wAttrmap
	ld a, BATTLE_MOVE_INFO_TYPE_ICON_ATTR
	call Icon_Set4x1Attrs

	hlcoord BATTLE_MOVE_INFO_CATEGORY_ICON_X, BATTLE_MOVE_INFO_CATEGORY_ICON_Y, wAttrmap
	ld a, BATTLE_MOVE_INFO_STAT_ICON_ATTR
	call Icon_Set2x2Attrs
	ret

MoveMenu_LoadAndDrawMoveIcons::
; Farcall-safe. Loads and draws the party move-detail type/category icons.
	call Icon_LoadCurrentMoveIconsGFX_Bank1
	farcall LoadMoveMenuCurrentIconPalettes

	hlcoord ICON_MOVE_MENU_TYPE_X, ICON_MOVE_MENU_Y
	ld a, ICON_MOVE_TYPE_TILE
	call Icon_Draw4x2

	hlcoord ICON_MOVE_MENU_CATEGORY_X, ICON_MOVE_MENU_Y
	ld a, ICON_MOVE_CATEGORY_TILE
	jp Icon_Draw4x2

MoveMenu_SetMoveIconAttrs::
	hlcoord ICON_MOVE_MENU_TYPE_X, ICON_MOVE_MENU_Y, wAttrmap
	ld a, $0e ; VRAM bank 1, BG palette 6
	call Icon_Set4x2Attrs

	hlcoord ICON_MOVE_MENU_CATEGORY_X, ICON_MOVE_MENU_Y, wAttrmap
	ld a, $0f ; VRAM bank 1, BG palette 7
	jp Icon_Set4x2Attrs
