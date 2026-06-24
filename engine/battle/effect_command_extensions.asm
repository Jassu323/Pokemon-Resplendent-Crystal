BattleCommand_StatFromEffectCommandExt:
	call BattleCommand_StatFromEffectExt
	ld a, [wBattleCommandFlags]
	bit BATTLE_CMD_FLAG_INVALID, a
	ret nz
	bit BATTLE_CMD_FLAG_STAT_DOWN, a
	jr nz, .stat_down
	ld a, [wBattleCommandParam]
	and $f
	cp EVASION
	jr z, .evasion_up
	call BattleCommand_ApplyStatParamExt
	farcall BattleCommand_LowerSub
	farcall BattleCommand_StatUpAnim
	farcall BattleCommand_RaiseSub
	farcall BattleCommand_StatUpMessage
	farcall BattleCommand_StatUpFailText
	ret

.evasion_up
	farcall BattleCommand_LowerSub
	call BattleCommand_ApplyStatParamExt
	farcall BattleCommand_StatUpAnim
	farcall BattleCommand_LowerSubNoAnim
	farcall BattleCommand_RaiseSub
	farcall BattleCommand_StatUpMessage
	farcall BattleCommand_StatUpFailText
	ret

.stat_down
	farcall BattleCommand_CheckHit
	call BattleCommand_ApplyStatParamExt
	ld a, [wBattleCommandAbort]
	and a
	ret nz
	farcall BattleCommand_LowerSub
	farcall BattleCommand_StatDownAnim
	farcall BattleCommand_RaiseSub
	farcall BattleCommand_StatDownMessage
	farcall BattleCommand_StatDownFailText
	ret

BattleCommand_ApplyStatParamExt:
	ld a, [wBattleCommandFlags]
	bit BATTLE_CMD_FLAG_INVALID, a
	ret nz
	bit BATTLE_CMD_FLAG_STAT_DOWN, a
	jr nz, .stat_down

	ld a, [wBattleCommandParam]
	ld b, a
	ld a, [wBattleCommandParam]
	bit 5, a ; STAT_PARAM_TARGET_OPP
	jr z, .raise_user
	ld a, b
	and STAT_PARAM_MASK
	ld b, a
	farcall BattleCommand_SwitchTurn
	farcall BattleCommand_StatUp
	farcall BattleCommand_SwitchTurn
	ret

.raise_user
	ld a, b
	and STAT_PARAM_MASK
	ld b, a
	farcall BattleCommand_StatUp
	ret

.stat_down
	ld a, [wBattleCommandParam]
	bit 5, a ; STAT_PARAM_TARGET_OPP
	jr z, .lower_user
	call BattleCommand_CheckCottonSporeGrassImmunityExt
	jr c, .blocked_by_powder
	farcall BattleCommand_StatDownFromParam
	ret

.lower_user
	farcall LowerStatFromParam
	ret

.blocked_by_powder
	farcall AnimateFailedMove
	farcall PrintDoesntAffect
	farcall EndMoveEffect
	ret

BattleCommand_SecondaryEffectCommandExt:
	ld a, [wBattleCommandParam2]
	and a
	jr nz, .got_effect
	call BattleCommand_SecondaryEffectExt
	ld a, [wBattleCommandFlags]
	bit BATTLE_CMD_FLAG_INVALID, a
	ret nz
	bit BATTLE_CMD_FLAG_SECONDARY_STAT, a
	jr nz, .stat
	ld a, [wBattleCommandParam2]

.got_effect
	cp SECONDARY_POISON
	jr z, .poison
	cp SECONDARY_BURN
	jr z, .burn
	cp SECONDARY_FREEZE
	jr z, .freeze
	cp SECONDARY_PARALYZE
	jr z, .paralyze
	cp SECONDARY_FLINCH
	jr z, .flinch
	cp SECONDARY_CONFUSE
	jr z, .confuse
	cp SECONDARY_ALL_STATS_UP
	jr z, .all_stats_up
	cp SECONDARY_TOXIC
	jr z, .toxic
	ret

.poison
	ld a, STATUS_POISON
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_PoisonTarget
	ret

.burn
	ld a, STATUS_BURN
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_BurnTarget
	ret

.freeze
	ld a, STATUS_FREEZE
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_FreezeTarget
	ret

.paralyze
	ld a, STATUS_PARALYZE
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_ParalyzeTarget
	ret

.flinch
	farcall BattleCommand_FlinchTarget
	ret

.confuse
	farcall BattleCommand_ConfuseTarget
	ret

.all_stats_up
	call BattleCommand_AllStatsUpExt
	ret

.toxic
	ld a, STATUS_TOXIC
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	call BattleCommand_ToxicTargetExt
	ret

.stat
	call BattleCommand_ApplyStatParamExt
	ld a, [wBattleCommandFlags]
	bit BATTLE_CMD_FLAG_STAT_DOWN, a
	jr nz, .stat_down_message
	farcall BattleCommand_StatUpMessage
	ret

.stat_down_message
	farcall BattleCommand_StatDownMessage
	ret

BattleCommand_ToxicTargetExt:
	farcall CheckSubstituteOpp
	ret nz
	ld a, BATTLE_VARS_STATUS_OPP
	call GetBattleVarAddr
	and a
	ret nz
	farcall GetOpponentItem
	ld a, b
	cp HELD_PREVENT_POISON
	ret z
	ld a, [wEffectFailed]
	and a
	ret nz
	farcall SafeCheckSafeguard
	ret nz
	ld a, BATTLE_VARS_SUBSTATUS5_OPP
	call GetBattleVarAddr
	set SUBSTATUS_TOXIC, [hl]
	ld de, wEnemyToxicCount
	ldh a, [hBattleTurn]
	and a
	jr z, .got_toxic_count
	ld de, wPlayerToxicCount

.got_toxic_count
	xor a
	ld [de], a
	ld a, BATTLE_VARS_STATUS_OPP
	call GetBattleVarAddr
	set PSN, [hl]
	call UpdateOpponentInParty
	ld de, ANIM_PSN
	farcall PlayOpponentBattleAnim
	call RefreshBattleHuds
	ld hl, BadlyPoisonedText
	call StdBattleTextbox
	farcall UseHeldStatusHealingItem
	ret

BattleCommand_AllStatsUpExt:
; Attack
	call .ResetMiss
	farcall BattleCommand_AttackUp
	farcall BattleCommand_StatUpMessage

; Defense
	call .ResetMiss
	farcall BattleCommand_DefenseUp
	farcall BattleCommand_StatUpMessage

; Speed
	call .ResetMiss
	farcall BattleCommand_SpeedUp
	farcall BattleCommand_StatUpMessage

; Special Attack
	call .ResetMiss
	farcall BattleCommand_SpecialAttackUp
	farcall BattleCommand_StatUpMessage

; Special Defense
	call .ResetMiss
	farcall BattleCommand_SpecialDefenseUp
	farcall BattleCommand_StatUpMessage
	ret

.ResetMiss:
	xor a
	ld [wAttackMissed], a
	ret

BattleCommand_TriStatusChanceExt:
	farcall BattleCommand_EffectChance
.loop
	; 1/3 chance of each status
	call BattleRandom
	swap a
	and %11
	jr z, .loop
	dec a
	ld hl, .StatusCommands
	rst JumpTable
	ret

.StatusCommands:
	dw .paralyze
	dw .freeze
	dw .burn

.paralyze
	ld a, STATUS_PARALYZE
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_ParalyzeTarget
	ret

.freeze
	ld a, STATUS_FREEZE
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_FreezeTarget
	ret

.burn
	ld a, STATUS_BURN
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_BurnTarget
	ret

BattleCommand_SecondaryStatusPrecheckExt:
	ld [wBattleCommandParam], a
	ld a, STATUS_CONTEXT_SECONDARY
	ld [wBattleCommandScratch], a
	call BattleCommand_StatusPrecheckExt
	ret

BattleCommand_StatusPrecheckExt:
	ld a, [wBattleCommandScratch]
	cp STATUS_CONTEXT_SECONDARY
	jr z, .got_status
	call BattleCommand_StatusFromEffectExt

.got_status
	xor a ; STATUS_BLOCK_GENERIC
	ld [wBattleCommandParam2], a
	ld a, [wBattleCommandScratch]
	cp STATUS_CONTEXT_SECONDARY
	jr z, .check_regular_immunity
	call BattleCommand_CheckPowderGrassImmunityExt
	jr c, .blocked

.check_regular_immunity
	call BattleCommand_CheckStatusImmunityExt
	jr c, .blocked
	and a
	ret

.blocked
	ld a, [wBattleCommandScratch]
	cp STATUS_CONTEXT_SECONDARY
	jr z, .secondary_blocked
	farcall AnimateFailedMove
	farcall BattleCommand_PrintStatusBlockText
	farcall EndMoveEffect

.secondary_blocked
	scf
	ret

BattleCommand_StatusTargetExt:
	ld a, [wBattleCommandParam]
	cp STATUS_FROM_EFFECT
	jr nz, .got_status
	call BattleCommand_StatusFromEffectExt

.got_status
	ld a, [wBattleCommandParam]
	cp STATUS_SLEEP
	jr z, .sleep
	cp STATUS_POISON
	jr z, .poison
	cp STATUS_TOXIC
	jr z, .poison
	cp STATUS_PARALYZE
	jr z, .paralyze
	cp STATUS_BURN
	jr z, .burn
	ret

.sleep
	farcall BattleCommand_SleepTarget
	ret

.poison
	farcall BattleCommand_Poison
	ret

.paralyze
	farcall BattleCommand_Paralyze
	ret

.burn
	farcall BattleCommand_Burn
	ret

BattleCommand_StatusFromEffectExt:
	ld a, BATTLE_VARS_MOVE_EFFECT
	call GetBattleVar
	cp EFFECT_SLEEP
	jr z, .sleep
	cp EFFECT_POISON
	jr z, .poison
	cp EFFECT_TOXIC
	jr z, .toxic
	cp EFFECT_PARALYZE
	jr z, .paralyze
	cp EFFECT_BURN
	jr z, .burn
	ld a, STATUS_FROM_EFFECT
	jr .store

.sleep
	ld a, STATUS_SLEEP
	jr .store

.poison
	ld a, STATUS_POISON
	jr .store

.toxic
	ld a, STATUS_TOXIC
	jr .store

.paralyze
	ld a, STATUS_PARALYZE
	jr .store

.burn
	ld a, STATUS_BURN

.store
	ld [wBattleCommandParam], a
	ret

BattleCommand_CheckStatusImmunityExt:
	ld a, [wBattleCommandScratch]
	cp STATUS_CONTEXT_SECONDARY
	jr nz, .check_status
	ld a, [wTypeModifier]
	and EFFECTIVENESS_MASK
	jr z, .blocked

.check_status
	ld a, [wBattleCommandParam]
	cp STATUS_POISON
	jr z, .poison
	cp STATUS_TOXIC
	jr z, .poison
	cp STATUS_PARALYZE
	jr z, .paralyze
	cp STATUS_BURN
	jr z, .burn
	cp STATUS_FREEZE
	jr z, .freeze
	and a
	ret

.poison
	ld c, POISON
	call BattleCommand_TargetHasTypeExt
	ret c
	ld c, STEEL
	jp BattleCommand_TargetHasTypeExt

.paralyze
	ld c, ELECTRIC
	call BattleCommand_TargetHasTypeExt
	ret c
	ld c, ELECTRIC
	call BattleCommand_MoveTypeMatchesExt
	jr nc, .paralyze_normal
	ld c, GROUND
	jp BattleCommand_TargetHasTypeExt

.paralyze_normal
	ld c, NORMAL
	call BattleCommand_MoveTypeMatchesExt
	ret nc
	ld c, GHOST
	jp BattleCommand_TargetHasTypeExt

.burn
	ld c, FIRE
	call BattleCommand_TargetHasTypeExt
	ret c
	ld a, [wBattleWeather]
	cp WEATHER_RAIN
	jr z, .rain_blocked
	and a
	ret

.freeze
	ld c, FIRE
	call BattleCommand_TargetHasTypeExt
	ret c
	ld c, ICE
	call BattleCommand_TargetHasTypeExt
	ret c
	ld a, [wBattleWeather]
	cp WEATHER_SUN
	jr z, .sun_blocked
	and a
	ret

.rain_blocked
	ld a, STATUS_BLOCK_RAIN
	ld [wBattleCommandParam2], a
	jr .blocked

.sun_blocked
	ld a, STATUS_BLOCK_SUN
	ld [wBattleCommandParam2], a
	; fallthrough

.blocked
	scf
	ret

BattleCommand_MoveTypeMatchesExt:
	ld a, BATTLE_VARS_MOVE_TYPE
	call GetBattleVar
	cp c
	jr z, .match
	and a
	ret

.match
	scf
	ret

BattleCommand_TargetHasTypeExt:
	ld hl, wEnemyMonType1
	ldh a, [hBattleTurn]
	and a
	jr z, .got_target
	ld hl, wBattleMonType1

.got_target
	ld a, [hli]
	cp c
	jr z, .match
	ld a, [hl]
	cp c
	jr z, .match
	and a
	ret

.match
	scf
	ret

BattleCommand_CheckPowderGrassImmunityExt:
	call BattleCommand_IsPowderMoveExt
	ret nc
	ld c, GRASS
	jp BattleCommand_TargetHasTypeExt

BattleCommand_CheckCottonSporeGrassImmunityExt:
	ld a, [wAttackMissed]
	and a
	ret nz
	ld hl, .CottonSporeMove
	call BattleCommand_CurrentMoveInListExt
	ret nc
	ld c, GRASS
	jp BattleCommand_TargetHasTypeExt

.CottonSporeMove:
	dw COTTON_SPORE
	dw -1

BattleCommand_IsPowderMoveExt:
	ld hl, .PowderMoves
	jr BattleCommand_CurrentMoveInListExt

.PowderMoves:
	dw POISONPOWDER
	dw SLEEP_POWDER
	dw SPORE
	dw STUN_SPORE
	dw COTTON_SPORE
	dw -1

BattleCommand_CurrentMoveInListExt:
	push hl
	ld a, BATTLE_VARS_MOVE_ANIM
	call GetBattleVar
	call GetMoveIndexFromID
	ld b, h
	ld c, l
	pop hl
	ld de, 2
	jp IsInWordArray

BattleCommand_StatFromEffectExt:
	xor a
	ld [wBattleCommandFlags], a
	ld a, BATTLE_VARS_MOVE_EFFECT
	call GetBattleVar

	cp EFFECT_ATTACK_UP
	jr c, .check_down_1
	cp EFFECT_EVASION_UP + 1
	jr nc, .check_down_1
	sub EFFECT_ATTACK_UP
	jr .store_up

.check_down_1
	cp EFFECT_ATTACK_DOWN
	jr c, .check_up_2
	cp EFFECT_EVASION_DOWN + 1
	jr nc, .check_up_2
	sub EFFECT_ATTACK_DOWN
	jr .store_down

.check_up_2
	cp EFFECT_ATTACK_UP_2
	jr c, .check_down_2
	cp EFFECT_EVASION_UP_2 + 1
	jr nc, .check_down_2
	sub EFFECT_ATTACK_UP_2
	or STAT_PARAM_STAGE_2
	jr .store_up

.check_down_2
	cp EFFECT_ATTACK_DOWN_2
	jr c, .invalid
	cp EFFECT_EVASION_DOWN_2 + 1
	jr nc, .invalid
	sub EFFECT_ATTACK_DOWN_2
	or STAT_PARAM_STAGE_2
	; fallthrough

.store_down
	or STAT_PARAM_TARGET_OPP
	ld [wBattleCommandParam], a
	ld a, 1 << BATTLE_CMD_FLAG_STAT_DOWN
	ld [wBattleCommandFlags], a
	ret

.store_up
	ld [wBattleCommandParam], a
	ret

.invalid
	ld a, 1 << BATTLE_CMD_FLAG_INVALID
	ld [wBattleCommandFlags], a
	ret

BattleCommand_SecondaryEffectExt:
	xor a
	ld [wBattleCommandFlags], a
	ld a, BATTLE_VARS_MOVE_EFFECT
	call GetBattleVar

	cp EFFECT_POISON_HIT
	jr z, .poison
	cp EFFECT_BURN_HIT
	jr z, .burn
	cp EFFECT_FREEZE_HIT
	jr z, .freeze
	cp EFFECT_BLIZZARD
	jr z, .freeze
	cp EFFECT_PARALYZE_HIT
	jr z, .paralyze
	cp EFFECT_THUNDER
	jr z, .paralyze
	cp EFFECT_FLINCH_HIT
	jr z, .flinch
	cp EFFECT_CONFUSE_HIT
	jr z, .confuse
	cp EFFECT_ALL_UP_HIT
	jr z, .all_stats_up

	cp EFFECT_ATTACK_DOWN_HIT
	jr c, .check_stat_up_hit
	cp EFFECT_EVASION_DOWN_HIT + 1
	jr nc, .check_stat_up_hit
	sub EFFECT_ATTACK_DOWN_HIT
	or STAT_PARAM_TARGET_OPP
	ld [wBattleCommandParam], a
	ld a, (1 << BATTLE_CMD_FLAG_SECONDARY_STAT) | (1 << BATTLE_CMD_FLAG_STAT_DOWN)
	ld [wBattleCommandFlags], a
	ret

.check_stat_up_hit
	cp EFFECT_DEFENSE_UP_HIT
	jr z, .defense_up
	cp EFFECT_ATTACK_UP_HIT
	jr z, .attack_up

.invalid
	ld a, 1 << BATTLE_CMD_FLAG_INVALID
	ld [wBattleCommandFlags], a
	ret

.poison
	ld bc, POISON_FANG
	call BattleCommand_CurrentMoveIsExt
	jr z, .poison_fang
	ld a, SECONDARY_POISON
	jr .store_secondary

.poison_fang
	ld a, SECONDARY_TOXIC
	jr .store_secondary

.burn
	ld a, SECONDARY_BURN
	jr .store_secondary

.freeze
	ld a, SECONDARY_FREEZE
	jr .store_secondary

.paralyze
	ld a, SECONDARY_PARALYZE
	jr .store_secondary

.flinch
	ld a, SECONDARY_FLINCH
	jr .store_secondary

.confuse
	ld a, SECONDARY_CONFUSE
	jr .store_secondary

.all_stats_up
	ld a, SECONDARY_ALL_STATS_UP
	jr .store_secondary

.defense_up
	ld a, DEFENSE
	jr .store_stat_up

.attack_up
	ld a, ATTACK
	; fallthrough

.store_stat_up
	ld [wBattleCommandParam], a
	ld a, 1 << BATTLE_CMD_FLAG_SECONDARY_STAT
	ld [wBattleCommandFlags], a
	ret

.store_secondary
	ld [wBattleCommandParam2], a
	ret

BattleCommand_FocusPunchExt:
	xor a
	ld [wBattleCommandAbort], a
	farcall BattleCommand_CheckObedience
	ld a, [wBattleCommandAbort]
	and a
	ret nz
	farcall BattleCommand_DoTurn
	ld a, [wBattleCommandAbort]
	and a
	ret nz
	call .check_lost_focus
	jr nz, .lost_focus
	farcall BattleCommand_UsedMoveText
	ret

.lost_focus
	ld hl, LostFocusText
	call StdBattleTextbox
	farcall EndMoveEffect
	ret

.check_lost_focus
	ld hl, wFocusPunchFlags
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy
	bit FOCUS_PUNCH_PLAYER_LOST, [hl]
	ret

.enemy
	bit FOCUS_PUNCH_ENEMY_LOST, [hl]
	ret

BattleCommand_BreakFocusPunchExt:
	ld hl, wFocusPunchFlags
	ldh a, [hBattleTurn]
	and a
	jr nz, .player_took_damage
	bit FOCUS_PUNCH_ENEMY_FOCUSING, [hl]
	ret z
	set FOCUS_PUNCH_ENEMY_LOST, [hl]
	ret

.player_took_damage
	bit FOCUS_PUNCH_PLAYER_FOCUSING, [hl]
	ret z
	set FOCUS_PUNCH_PLAYER_LOST, [hl]
	ret

BattleCommand_BattleExtDispatcher:
	ld a, [wBattleCommandParam]
	cp BATTLE_EXTCMD_TAUNT
	jp z, BattleCommand_TauntExt
	cp BATTLE_EXTCMD_WISH
	jp z, BattleCommand_WishExt
	cp BATTLE_EXTCMD_MULTI_STAT_UP
	jp z, BattleCommand_MultiStatUpExt
	cp BATTLE_EXTCMD_SELF_STAT_DROP_HIT
	jp z, BattleCommand_SelfStatDropHitExt
	cp BATTLE_EXTCMD_CURSE
	jp z, BattleCommand_CurseExt
	cp BATTLE_EXTCMD_FANG_HIT
	jp z, BattleCommand_FangHitExt
	cp BATTLE_EXTCMD_SUCKER_PUNCH
	jp z, BattleCommand_SuckerPunchExt
	cp BATTLE_EXTCMD_HEAVY_SLAM_POWER
	jp z, BattleCommand_HeavySlamPowerExt
	cp BATTLE_EXTCMD_INGRAIN
	jp z, BattleCommand_IngrainExt
	cp BATTLE_EXTCMD_BRICK_BREAK_ANIM
	jp z, BattleCommand_BrickBreakAnimExt
	cp BATTLE_EXTCMD_BRICK_BREAK
	jp z, BattleCommand_BrickBreakExt
	ret

BattleCommand_BrickBreakAnimExt:
	ld a, [wAttackMissed]
	and a
	jr nz, .failed
	ld a, [wEffectFailed]
	and a
	jr nz, .failed

	ld hl, wEnemyScreens
	ldh a, [hBattleTurn]
	and a
	jr z, .got_screens
	ld hl, wPlayerScreens

.got_screens
	xor a
	bit SCREENS_LIGHT_SCREEN, [hl]
	jr nz, .shatter
	bit SCREENS_REFLECT, [hl]
	jr z, .got_param

.shatter
	inc a

.got_param
	ld [wBattleAnimParam], a
	farcall AnimateCurrentMoveEitherSide
	ret

.failed
	farcall AnimateFailedMove
	ret

BattleCommand_BrickBreakExt:
	ld a, [wAttackMissed]
	and a
	ret nz
	ld a, [wEffectFailed]
	and a
	ret nz

	ld hl, wEnemyScreens
	ld de, wEnemyLightScreenCount
	ldh a, [hBattleTurn]
	and a
	jr z, .got_screens
	ld hl, wPlayerScreens
	ld de, wPlayerLightScreenCount

.got_screens
	xor a
	ld [wBattleCommandScratch], a
	bit SCREENS_LIGHT_SCREEN, [hl]
	jr z, .reflect
	res SCREENS_LIGHT_SCREEN, [hl]
	ld [de], a
	inc a
	ld [wBattleCommandScratch], a

.reflect
	bit SCREENS_REFLECT, [hl]
	jr z, .got_count
	res SCREENS_REFLECT, [hl]
	inc de
	xor a
	ld [de], a
	ld a, [wBattleCommandScratch]
	inc a
	ld [wBattleCommandScratch], a

.got_count
	ld a, [wBattleCommandScratch]
	and a
	ret z

	ld a, EFFECTIVE
	ld [wTypeModifier], a
	farcall BattleCommand_DamageStats
	farcall BattleCommand_DamageCalc
	farcall BattleCommand_Stab

	ld a, [wBattleCommandScratch]
	cp 2
	ld hl, BarrierDestroyedText
	jr nz, .got_text
	ld hl, BarriersDestroyedText

.got_text
	jp StdBattleTextbox

BattleCommand_IngrainExt:
	ld a, BATTLE_VARS_SUBSTATUS5
	call GetBattleVarAddr
	bit SUBSTATUS_INGRAIN, [hl]
	jr nz, .failed
	push hl
	farcall AnimateCurrentMove
	pop hl
	set SUBSTATUS_INGRAIN, [hl]
	ld hl, PlantedRootsText
	jp StdBattleTextbox

.failed
	farcall AnimateFailedMove
	farcall PrintButItFailed
	farcall EndMoveEffect
	ret

BattleCommand_SuckerPunchExt:
	ld a, [wEnemyGoesFirst]
	ld b, a
	ldh a, [hBattleTurn]
	xor b
	jr nz, .failed
	ld hl, wEnemyMoveStruct + MOVE_POWER
	ldh a, [hBattleTurn]
	and a
	jr z, .got_power
	ld hl, wPlayerMoveStruct + MOVE_POWER

.got_power
	ld a, [hl]
	and a
	ret nz

.failed
	farcall AnimateFailedMove
	farcall PrintButItFailed
	farcall EndMoveEffect
	ret

BattleCommand_HeavySlamPowerExt:
	push bc
	push de
	call .GetUserWeight
	ld de, wStringBuffer1
	call .StoreHL
	call .GetTargetWeight
	ld de, wStringBuffer3
	call .StoreHL

	lb bc, 5, 120
	call .TryWeightRatio
	jr c, .done
	lb bc, 4, 100
	call .TryWeightRatio
	jr c, .done
	lb bc, 3, 80
	call .TryWeightRatio
	jr c, .done
	lb bc, 2, 60
	call .TryWeightRatio
	jr c, .done

	ld a, 40
	ld [wTextDecimalByte], a

.done
	pop de
	pop bc
	ld a, [wTextDecimalByte]
	ld d, a
	ret

.GetUserWeight:
	ldh a, [hBattleTurn]
	and a
	ld a, [wBattleMonSpecies]
	jr z, .got_species
	ld a, [wEnemyMonSpecies]
	jr .got_species

.GetTargetWeight:
	ldh a, [hBattleTurn]
	and a
	ld a, [wEnemyMonSpecies]
	jr z, .got_species
	ld a, [wBattleMonSpecies]

.got_species
	call .GetSpeciesWeight
	ret

.GetSpeciesWeight:
	call GetPokemonIndexFromID
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
	ld de, PokedexDataPointerTable
	add hl, de
	ld a, BANK(PokedexDataPointerTable)
	call GetFarByte
	push af
	inc hl
	ld a, BANK(PokedexDataPointerTable)
	call GetFarWord
	pop de

.skip_species_name
	ld a, d
	call GetFarByte
	inc hl
	cp '@'
	jr nz, .skip_species_name
	ld a, d
	inc hl
	inc hl
	call GetFarWord
	ret

.StoreHL:
	ld a, h
	ld [de], a
	inc de
	ld a, l
	ld [de], a
	ret

.TryWeightRatio:
	push bc
	call .BuildThreshold
	call .UserAtLeastThreshold
	pop bc
	ret nc
	ld a, c
	ld [wTextDecimalByte], a
	ld d, a
	scf
	ret

.BuildThreshold:
	ld a, [wStringBuffer3]
	ld d, a
	ld a, [wStringBuffer3 + 1]
	ld e, a
	ld h, d
	ld l, e
	dec b
	ret z

.multiply_loop
	add hl, de
	jr nc, .no_overflow
	ld hl, $ffff
	ret

.no_overflow
	dec b
	jr nz, .multiply_loop
	ret

.UserAtLeastThreshold:
	ld a, [wStringBuffer1]
	cp h
	jr c, .less
	jr nz, .greater
	ld a, [wStringBuffer1 + 1]
	cp l
	jr c, .less

.greater
	scf
	ret

.less
	and a
	ret

BattleCommand_FangHitExt:
	farcall BattleCommand_EffectChance
	ld a, [wEffectFailed]
	and a
	jr nz, .status
	farcall BattleCommand_FlinchTarget

.status
	farcall BattleCommand_EffectChance
	ld a, [wEffectFailed]
	and a
	ret nz
	ld bc, THUNDER_FANG
	call BattleCommand_CurrentMoveIsExt
	jr z, .paralyze
	ld bc, ICE_FANG
	call BattleCommand_CurrentMoveIsExt
	jr z, .freeze
	ld bc, FIRE_FANG
	call BattleCommand_CurrentMoveIsExt
	jr z, .burn
	ret

.paralyze
	ld a, STATUS_PARALYZE
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_ParalyzeTarget
	ret

.freeze
	ld a, STATUS_FREEZE
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_FreezeTarget
	ret

.burn
	ld a, STATUS_BURN
	call BattleCommand_SecondaryStatusPrecheckExt
	ret c
	farcall BattleCommand_BurnTarget
	ret

BattleCommand_MultiStatUpExt:
	ld bc, BULK_UP
	call BattleCommand_CurrentMoveIsExt
	jr z, .bulk_up
	ld bc, CALM_MIND
	call BattleCommand_CurrentMoveIsExt
	jr z, .calm_mind
	ld bc, DRAGON_DANCE
	call BattleCommand_CurrentMoveIsExt
	jr z, .dragon_dance
	ret

.bulk_up
	lb bc, ATTACK, DEFENSE
	jr BattleCommand_DoubleStatUpExt

.calm_mind
	lb bc, SP_ATTACK, SP_DEFENSE
	jr BattleCommand_DoubleStatUpExt

.dragon_dance
	lb bc, ATTACK, SPEED
	; fallthrough

BattleCommand_DoubleStatUpExt:
	push bc
	ld a, b
	call BattleCommand_ActorStatCanRiseExt
	pop bc
	jr c, .can_raise
	push bc
	ld a, c
	call BattleCommand_ActorStatCanRiseExt
	pop bc
	jr c, .can_raise
	farcall AnimateFailedMove
	ld hl, StatsWontRiseAnymoreText
	jp StdBattleTextbox

.can_raise
	push bc
	farcall AnimateCurrentMove
	pop bc
	push bc
	ld a, b
	call BattleCommand_TryUserStatUpExt
	pop bc
	ld a, c
	jp BattleCommand_TryUserStatUpExt

BattleCommand_SelfStatDropHitExt:
	ld a, [wAttackMissed]
	and a
	ret nz
	ld a, [wEffectFailed]
	and a
	ret nz
	ld bc, SUPERPOWER
	call BattleCommand_CurrentMoveIsExt
	jr z, .superpower
	ld bc, OVERHEAT
	call BattleCommand_CurrentMoveIsExt
	jr z, .overheat
	ret

.superpower
	ld a, ATTACK
	call BattleCommand_ActorStatCanFallExt
	jr c, .superpower_anim
	ld a, DEFENSE
	call BattleCommand_ActorStatCanFallExt
	jr nc, .superpower_apply

.superpower_anim
	xor a
	call BattleCommand_PlayUserStatDownAnimExt

.superpower_apply
	ld a, ATTACK
	call BattleCommand_TryUserStatDownExt
	ld a, DEFENSE
	call BattleCommand_TryUserStatDownExt
	jp BattleCommand_ResetStatFailureExt

.overheat
	ld a, SP_ATTACK
	call BattleCommand_ActorStatCanFallExt
	jr nc, .overheat_apply
	ld a, STAT_PARAM_STAGE_2
	call BattleCommand_PlayUserStatDownAnimExt

.overheat_apply
	ld a, STAT_PARAM_STAGE_2 | SP_ATTACK
	call BattleCommand_TryUserStatDownExt
	jp BattleCommand_ResetStatFailureExt

BattleCommand_CurseExt:
	call BattleCommand_UserIsGhostExt
	jr c, .ghost

; Preserve Crystal behavior: non-Ghost Curse only checks Attack/Defense.
	ld a, ATTACK
	call BattleCommand_ActorStatCanRiseExt
	jr c, .raise
	ld a, DEFENSE
	call BattleCommand_ActorStatCanRiseExt
	jr c, .raise

	ld b, ABILITY + 1
	farcall GetStatName
	farcall AnimateFailedMove
	ld hl, WontRiseAnymoreText
	jp StdBattleTextbox

.raise
	ld a, $1
	ld [wBattleAnimParam], a
	farcall AnimateCurrentMove
	ld a, SPEED
	call BattleCommand_TryUserStatDownExt
	ld a, ATTACK
	call BattleCommand_TryUserStatUpExt
	ld a, DEFENSE
	jp BattleCommand_TryUserStatUpExt

.ghost
	farcall CheckHiddenOpponent
	jr nz, .failed

	farcall CheckSubstituteOpp
	jr nz, .failed

	ld a, BATTLE_VARS_SUBSTATUS1_OPP
	call GetBattleVarAddr
	bit SUBSTATUS_CURSE, [hl]
	jr nz, .failed

	set SUBSTATUS_CURSE, [hl]
	farcall AnimateCurrentMove
	farcall GetHalfMaxHP
	farcall SubtractHPFromUser
	call UpdateUserInParty
	ld hl, PutACurseText
	jp StdBattleTextbox

.failed
	farcall AnimateFailedMove
	farcall PrintButItFailed
	ret

BattleCommand_CurrentMoveIsExt:
	push bc
	ld a, BATTLE_VARS_MOVE
	call GetBattleVar
	call GetMoveIndexFromID
	pop bc
	ld a, h
	cp b
	ret nz
	ld a, l
	cp c
	ret

BattleCommand_GetActorStatLevelsExt:
	ld hl, wPlayerStatLevels
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyStatLevels
	ret

BattleCommand_ActorStatCanRiseExt:
	push af
	call BattleCommand_GetActorStatLevelsExt
	pop af
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [hl]
	cp MAX_STAT_LEVEL
	ret

BattleCommand_ActorStatCanFallExt:
	push af
	call BattleCommand_GetActorStatLevelsExt
	pop af
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [hl]
	cp 2
	ccf
	ret

BattleCommand_TryUserStatUpExt:
	push af
	call BattleCommand_ResetStatFailureExt
	xor a
	ld [wBattleCommandFlags], a
	pop af
	ld [wBattleCommandParam], a
	call BattleCommand_ApplyStatParamExt
	farcall BattleCommand_StatUpMessage
	ret

BattleCommand_TryUserStatDownExt:
	push af
	call BattleCommand_ResetStatFailureExt
	ld a, 1 << BATTLE_CMD_FLAG_STAT_DOWN
	ld [wBattleCommandFlags], a
	pop af
	ld [wBattleCommandParam], a
	call BattleCommand_ApplyStatParamExt
	farcall BattleCommand_SwitchTurn
	farcall BattleCommand_StatDownMessage
	farcall BattleCommand_SwitchTurn
	ret

BattleCommand_PlayUserStatDownAnimExt:
	ld [wBattleAnimParam], a
	xor a
	ld [wBattleAfterAnim], a
	call BattleCore_SwitchTurn
	ld a, LOW(ANIM_STAT_DOWN)
	ld [wFXAnimID], a
	ld a, HIGH(ANIM_STAT_DOWN)
	ld [wFXAnimID + 1], a
	predef PlayBattleAnim
	jp BattleCore_SwitchTurn

BattleCommand_ResetStatFailureExt:
	xor a
	ld [wAttackMissed], a
	ld [wFailedMessage], a
	ret

BattleCommand_UserIsGhostExt:
	ld hl, wBattleMonType1
	ldh a, [hBattleTurn]
	and a
	jr z, .check_type_1
	ld hl, wEnemyMonType1

.check_type_1
	ld a, [hli]
	cp GHOST
	jr z, .is_ghost
	ld a, [hl]
	cp GHOST
	jr z, .is_ghost
	and a
	ret

.is_ghost
	scf
	ret

BattleCommand_TauntExt:
	call BattleCore_GetOpponentTauntCount
	ld a, [hl]
	and a
	jr nz, .failed
	push hl
	farcall AnimateCurrentMove
	pop hl
	ld [hl], 4
	ld hl, WasTauntedText
	call StdBattleTextbox
	ret

.failed
	ld hl, AlreadyTauntedText
	call StdBattleTextbox
	farcall EndMoveEffect
	ret

BattleCommand_WishExt:
	call BattleCore_GetActorWishCount
	ld a, [hl]
	and a
	jr nz, .failed

	push hl
	farcall GetHalfMaxHP
	pop hl
	ld [hl], 2

	call BattleCore_GetActorWishHP
	ld a, b
	ld [hli], a
	ld [hl], c
	call BattleCore_StoreActorWishName

	farcall AnimateCurrentMove
	ld hl, MadeWishText
	jp StdBattleTextbox

.failed
	farcall AnimateFailedMove
	farcall PrintButItFailed
	farcall EndMoveEffect
	ret

BattleCoreHookExt:
	ld a, [wBattleCommandParam]
	cp BATTLE_CORE_HOOK_BEFORE_ACTION
	jr z, BattleCore_BeforeActionExt
	cp BATTLE_CORE_HOOK_AFTER_ACTION
	jr z, BattleCore_AfterActionExt
	cp BATTLE_CORE_HOOK_BETWEEN_TURNS
	jr z, BattleCore_BetweenTurnsExt
	and a
	ret

BattleCore_BeforeActionExt:
	call BattleCore_CheckTauntBlock
	ret

BattleCore_AfterActionExt:
	call BattleCore_GetActorTauntCount
	ld a, [hl]
	and a
	ret z
	dec [hl]
	ret nz
	ld hl, TauntWoreOffText
	jp StdBattleTextbox

BattleCore_BetweenTurnsExt:
	ldh a, [hSerialConnectionStatus]
	cp USING_EXTERNAL_CLOCK
	jr z, .enemy_first
	call SetPlayerTurn
	call BattleCore_HandleWish
	call BattleCore_HandleIngrain
	call SetEnemyTurn
	call BattleCore_HandleWish
	jp BattleCore_HandleIngrain

.enemy_first
	call SetEnemyTurn
	call BattleCore_HandleWish
	call BattleCore_HandleIngrain
	call SetPlayerTurn
	call BattleCore_HandleWish
	; fallthrough

BattleCore_HandleIngrain:
	ld a, BATTLE_VARS_SUBSTATUS5
	call GetBattleVar
	bit SUBSTATUS_INGRAIN, a
	ret z
	call BattleCore_UserHPIsFull
	ret z
	farcall GetSixteenthMaxHP
	push bc
	call BattleCore_IngrainRecoveryAnim
	pop bc
	call BattleCore_SwitchTurn
	farcall RestoreHP
	call BattleCore_SwitchTurn
	call UpdateUserInParty
	call RefreshBattleHuds
	ld hl, AbsorbedNutrientsText
	jp StdBattleTextbox

BattleCore_HandleWish:
	call BattleCore_GetActorWishCount
	ld a, [hl]
	and a
	ret z
	dec [hl]
	ret nz

	call BattleCore_CopyActorWishNameToBuffer
	ld hl, WishCameTrueText
	call StdBattleTextbox

	call BattleCore_UserHPIsFull
	ret z

	call BattleCore_GetActorWishHP
	ld a, [hli]
	ld b, a
	ld a, [hl]
	ld c, a
	call BattleCore_WishRecoveryAnim
	call BattleCore_SwitchTurn
	farcall RestoreHP
	call BattleCore_SwitchTurn
	call UpdateUserInParty
	call RefreshBattleHuds
	ld hl, RegainedHealthText
	jp StdBattleTextbox

BattleCore_WishRecoveryAnim:
	push bc
	farcall EmptyBattleTextbox
	xor a
	ld [wBattleAfterAnim], a
	if HIGH(ANIM_WISH_HEAL)
		ld a, HIGH(ANIM_WISH_HEAL)
	endc
	ld [wFXAnimID + 1], a
	ld a, LOW(ANIM_WISH_HEAL)
	ld [wFXAnimID], a
	predef PlayBattleAnim
	pop bc
	ret

BattleCore_IngrainRecoveryAnim:
	farcall EmptyBattleTextbox
	xor a
	ld [wBattleAfterAnim], a
	if HIGH(INGRAIN)
		ld a, HIGH(INGRAIN)
	endc
	ld [wFXAnimID + 1], a
	ld a, LOW(INGRAIN)
	ld [wFXAnimID], a
	predef_jump PlayBattleAnim

BattleCore_UserHPIsFull:
	ld hl, wBattleMonHP
	ld de, wBattleMonMaxHP
	ldh a, [hBattleTurn]
	and a
	jr z, .got_hp
	ld hl, wEnemyMonHP
	ld de, wEnemyMonMaxHP

.got_hp
	ld a, [hli]
	ld b, a
	ld a, [de]
	cp b
	ret nz
	inc de
	ld a, [hl]
	ld b, a
	ld a, [de]
	cp b
	ret

BattleCore_SwitchTurn:
	ldh a, [hBattleTurn]
	xor 1
	ldh [hBattleTurn], a
	ret

BattleCore_CheckTauntBlock:
	call BattleCore_GetActorTauntCount
	ld a, [hl]
	and a
	jr z, .not_blocked
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy
	ld a, [wBattlePlayerAction]
	and a ; BATTLEPLAYERACTION_USEMOVE?
	jr nz, .not_blocked
	ld a, [wPlayerMoveStruct + MOVE_POWER]
	jr .got_power

.enemy
	ld a, [wEnemyMoveStruct + MOVE_POWER]

.got_power
	and a
	jr nz, .not_blocked
	ld a, BATTLE_VARS_MOVE
	call GetBattleVar
	ld [wNamedObjectIndex], a
	call GetMoveName
	ld hl, TauntPreventedMoveText
	call StdBattleTextbox
	scf
	ret

.not_blocked
	and a
	ret

BattleCore_GetActorTauntCount:
	ld hl, wPlayerTauntCount
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyTauntCount
	ret

BattleCore_GetOpponentTauntCount:
	ld hl, wEnemyTauntCount
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wPlayerTauntCount
	ret

BattleCore_GetActorWishCount:
	ld hl, wPlayerWishCount
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyWishCount
	ret

BattleCore_GetActorWishHP:
	ld hl, wPlayerWishHP
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyWishHP
	ret

BattleCore_GetActorWishName:
	ld hl, wPlayerWishUserName
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyWishUserName
	ret

BattleCore_StoreActorWishName:
	call BattleCore_GetActorWishName
	ld d, h
	ld e, l
	ld hl, wBattleMonNickname
	ldh a, [hBattleTurn]
	and a
	jr z, .copy
	ld hl, wEnemyMonNickname

.copy
	ld bc, MON_NAME_LENGTH
	jp CopyBytes

BattleCore_CopyActorWishNameToBuffer:
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy
	call BattleCore_GetActorWishName
	ld de, wStringBuffer1
	ld bc, MON_NAME_LENGTH
	jp CopyBytes

.enemy
	ld hl, EnemyText
	ld de, wStringBuffer1

.copy_prefix
	ld a, [hli]
	cp '@'
	jr z, .copy_name
	ld [de], a
	inc de
	jr .copy_prefix

.copy_name
	call BattleCore_GetActorWishName
	ld bc, MON_NAME_LENGTH
	jp CopyBytes
