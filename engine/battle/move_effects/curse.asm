BattleCommand_Curse:
	ld a, BATTLE_EXTCMD_CURSE
	ld [wBattleCommandParam], a
	farcall BattleCommand_BattleExtDispatcher
	ret
