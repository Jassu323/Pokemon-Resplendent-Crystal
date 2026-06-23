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
	ld a, SECONDARY_POISON
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

BattleCoreHookExt:
	ld a, [wBattleCommandParam]
	cp BATTLE_CORE_HOOK_BEFORE_ACTION
	jr z, BattleCore_BeforeActionExt
	cp BATTLE_CORE_HOOK_AFTER_ACTION
	jr z, BattleCore_AfterActionExt
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
