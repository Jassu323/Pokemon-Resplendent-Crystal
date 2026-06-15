; entries correspond to constants/move_constants.asm
:
	table_width 2, :-
; negative entries first, ordered from most-negative ID back toward -1
; (see the constants file for details)
	dw BattleAnim_InHail
	dw BattleAnim_InSun
	dw BattleAnim_InRain
	dw BattleAnim_ThrowPokeBall
	dw BattleAnim_SendOutMon
	dw BattleAnim_ReturnMon
	dw BattleAnim_Confused
	dw BattleAnim_Slp
	dw BattleAnim_Brn
	dw BattleAnim_Psn
	dw BattleAnim_Sap
	dw BattleAnim_Frz
	dw BattleAnim_Par
	dw BattleAnim_InLove
	dw BattleAnim_InSandstorm
	dw BattleAnim_InNightmare
	dw BattleAnim_InWhirlpool
	dw BattleAnim_Miss
	dw BattleAnim_EnemyDamage
	dw BattleAnim_StatDown
	dw BattleAnim_StatUp
	dw BattleAnim_PlayerDamage
	dw BattleAnim_Wobble
	dw BattleAnim_Shake
	dw BattleAnim_HitConfusion
	assert_table_length NUM_BATTLE_ANIMS
BattleAnimations::
	table_width 2
	dw BattleAnim_Dummy
	dw BattleAnim_Pound
	dw BattleAnim_KarateChop
	dw BattleAnim_Doubleslap
	dw BattleAnim_CometPunch
	dw BattleAnim_MegaPunch
	dw BattleAnim_PayDay
	dw BattleAnim_FirePunch
	dw BattleAnim_IcePunch
	dw BattleAnim_Thunderpunch
	dw BattleAnim_Scratch
	dw BattleAnim_Vicegrip
	dw BattleAnim_Guillotine
	dw BattleAnim_RazorWind
	dw BattleAnim_SwordsDance
	dw BattleAnim_Cut
	dw BattleAnim_Gust
	dw BattleAnim_WingAttack
	dw BattleAnim_Whirlwind
	dw BattleAnim_Fly
	dw BattleAnim_Bind
	dw BattleAnim_Slam
	dw BattleAnim_VineWhip
	dw BattleAnim_Stomp
	dw BattleAnim_DoubleKick
	dw BattleAnim_MegaKick
	dw BattleAnim_JumpKick
	dw BattleAnim_RollingKick
	dw BattleAnim_SandAttack
	dw BattleAnim_Headbutt
	dw BattleAnim_HornAttack
	dw BattleAnim_FuryAttack
	dw BattleAnim_HornDrill
	dw BattleAnim_Tackle
	dw BattleAnim_BodySlam
	dw BattleAnim_Wrap
	dw BattleAnim_TakeDown
	dw BattleAnim_Thrash
	dw BattleAnim_DoubleEdge
	dw BattleAnim_TailWhip
	dw BattleAnim_PoisonSting
	dw BattleAnim_Twineedle
	dw BattleAnim_PinMissile
	dw BattleAnim_Leer
	dw BattleAnim_Bite
	dw BattleAnim_Growl
	dw BattleAnim_Roar
	dw BattleAnim_Sing
	dw BattleAnim_Supersonic
	dw BattleAnim_Sonicboom
	dw BattleAnim_Disable
	dw BattleAnim_Acid
	dw BattleAnim_Ember
	dw BattleAnim_Flamethrower
	dw BattleAnim_Mist
	dw BattleAnim_WaterGun
	dw BattleAnim_HydroPump
	dw BattleAnim_Surf
	dw BattleAnim_IceBeam
	dw BattleAnim_Blizzard
	dw BattleAnim_Psybeam
	dw BattleAnim_Bubblebeam
	dw BattleAnim_AuroraBeam
	dw BattleAnim_HyperBeam
	dw BattleAnim_Peck
	dw BattleAnim_DrillPeck
	dw BattleAnim_Submission
	dw BattleAnim_LowKick
	dw BattleAnim_Counter
	dw BattleAnim_SeismicToss
	dw BattleAnim_Strength
	dw BattleAnim_Absorb
	dw BattleAnim_MegaDrain
	dw BattleAnim_LeechSeed
	dw BattleAnim_Growth
	dw BattleAnim_RazorLeaf
	dw BattleAnim_Solarbeam
	dw BattleAnim_Poisonpowder
	dw BattleAnim_StunSpore
	dw BattleAnim_SleepPowder
	dw BattleAnim_PetalDance
	dw BattleAnim_StringShot
	dw BattleAnim_DragonRage
	dw BattleAnim_FireSpin
	dw BattleAnim_Thundershock
	dw BattleAnim_Thunderbolt
	dw BattleAnim_ThunderWave
	dw BattleAnim_Thunder
	dw BattleAnim_RockThrow
	dw BattleAnim_Earthquake
	dw BattleAnim_Fissure
	dw BattleAnim_Dig
	dw BattleAnim_Toxic
	dw BattleAnim_Confusion
	dw BattleAnim_PsychicM
	dw BattleAnim_Hypnosis
	dw BattleAnim_Meditate
	dw BattleAnim_Agility
	dw BattleAnim_QuickAttack
	dw BattleAnim_Rage
	dw BattleAnim_Teleport
	dw BattleAnim_NightShade
	dw BattleAnim_Mimic
	dw BattleAnim_Screech
	dw BattleAnim_DoubleTeam
	dw BattleAnim_Recover
	dw BattleAnim_Harden
	dw BattleAnim_Minimize
	dw BattleAnim_Smokescreen
	dw BattleAnim_ConfuseRay
	dw BattleAnim_Withdraw
	dw BattleAnim_DefenseCurl
	dw BattleAnim_Barrier
	dw BattleAnim_LightScreen
	dw BattleAnim_Haze
	dw BattleAnim_Reflect
	dw BattleAnim_FocusEnergy
	dw BattleAnim_Bide
	dw BattleAnim_Metronome
	dw BattleAnim_MirrorMove
	dw BattleAnim_Selfdestruct
	dw BattleAnim_EggBomb
	dw BattleAnim_Lick
	dw BattleAnim_Smog
	dw BattleAnim_Sludge
	dw BattleAnim_BoneClub
	dw BattleAnim_FireBlast
	dw BattleAnim_Waterfall
	dw BattleAnim_Clamp
	dw BattleAnim_Swift
	dw BattleAnim_SkullBash
	dw BattleAnim_SpikeCannon
	dw BattleAnim_Constrict
	dw BattleAnim_Amnesia
	dw BattleAnim_Kinesis
	dw BattleAnim_Softboiled
	dw BattleAnim_HiJumpKick
	dw BattleAnim_Glare
	dw BattleAnim_DreamEater
	dw BattleAnim_PoisonGas
	dw BattleAnim_Barrage
	dw BattleAnim_LeechLife
	dw BattleAnim_LovelyKiss
	dw BattleAnim_SkyAttack
	dw BattleAnim_Transform
	dw BattleAnim_Bubble
	dw BattleAnim_DizzyPunch
	dw BattleAnim_Spore
	dw BattleAnim_Flash
	dw BattleAnim_Psywave
	dw BattleAnim_Splash
	dw BattleAnim_AcidArmor
	dw BattleAnim_Crabhammer
	dw BattleAnim_Explosion
	dw BattleAnim_FurySwipes
	dw BattleAnim_Bonemerang
	dw BattleAnim_Rest
	dw BattleAnim_RockSlide
	dw BattleAnim_HyperFang
	dw BattleAnim_Sharpen
	dw BattleAnim_Conversion
	dw BattleAnim_TriAttack
	dw BattleAnim_SuperFang
	dw BattleAnim_Slash
	dw BattleAnim_Substitute
	dw BattleAnim_Struggle
	dw BattleAnim_Sketch
	dw BattleAnim_TripleKick
	dw BattleAnim_Thief
	dw BattleAnim_SpiderWeb
	dw BattleAnim_MindReader
	dw BattleAnim_Nightmare
	dw BattleAnim_FlameWheel
	dw BattleAnim_Snore
	dw BattleAnim_Curse
	dw BattleAnim_Flail
	dw BattleAnim_Conversion2
	dw BattleAnim_Aeroblast
	dw BattleAnim_CottonSpore
	dw BattleAnim_Reversal
	dw BattleAnim_Spite
	dw BattleAnim_PowderSnow
	dw BattleAnim_Protect
	dw BattleAnim_MachPunch
	dw BattleAnim_ScaryFace
	dw BattleAnim_FaintAttack
	dw BattleAnim_SweetKiss
	dw BattleAnim_BellyDrum
	dw BattleAnim_SludgeBomb
	dw BattleAnim_MudSlap
	dw BattleAnim_Octazooka
	dw BattleAnim_Spikes
	dw BattleAnim_ZapCannon
	dw BattleAnim_Foresight
	dw BattleAnim_DestinyBond
	dw BattleAnim_PerishSong
	dw BattleAnim_IcyWind
	dw BattleAnim_Detect
	dw BattleAnim_BoneRush
	dw BattleAnim_LockOn
	dw BattleAnim_Outrage
	dw BattleAnim_Sandstorm
	dw BattleAnim_GigaDrain
	dw BattleAnim_Endure
	dw BattleAnim_Charm
	dw BattleAnim_Rollout
	dw BattleAnim_FalseSwipe
	dw BattleAnim_Swagger
	dw BattleAnim_MilkDrink
	dw BattleAnim_Spark
	dw BattleAnim_FuryCutter
	dw BattleAnim_SteelWing
	dw BattleAnim_MeanLook
	dw BattleAnim_Attract
	dw BattleAnim_SleepTalk
	dw BattleAnim_HealBell
	dw BattleAnim_Return
	dw BattleAnim_Present
	dw BattleAnim_Frustration
	dw BattleAnim_Safeguard
	dw BattleAnim_PainSplit
	dw BattleAnim_SacredFire
	dw BattleAnim_Magnitude
	dw BattleAnim_Dynamicpunch
	dw BattleAnim_Megahorn
	dw BattleAnim_Dragonbreath
	dw BattleAnim_BatonPass
	dw BattleAnim_Encore
	dw BattleAnim_Pursuit
	dw BattleAnim_RapidSpin
	dw BattleAnim_SweetScent
	dw BattleAnim_IronTail
	dw BattleAnim_MetalClaw
	dw BattleAnim_VitalThrow
	dw BattleAnim_MorningSun
	dw BattleAnim_Synthesis
	dw BattleAnim_Moonlight
	dw BattleAnim_HiddenPower
	dw BattleAnim_CrossChop
	dw BattleAnim_Twister
	dw BattleAnim_RainDance
	dw BattleAnim_SunnyDay
	dw BattleAnim_Crunch
	dw BattleAnim_MirrorCoat
	dw BattleAnim_PsychUp
	dw BattleAnim_Extremespeed
	dw BattleAnim_Ancientpower
	dw BattleAnim_ShadowBall
	dw BattleAnim_FutureSight
	dw BattleAnim_RockSmash
	dw BattleAnim_Whirlpool
	dw BattleAnim_Tackle ; placeholder from Beat Up
	dw BattleAnim_FakeOut
	dw BattleAnim_HeatWave
	dw BattleAnim_Hail
	dw BattleAnim_WillOWisp
	dw BattleAnim_FocusPunch
	dw BattleAnim_Taunt
	dw BattleAnim_Wish
	dw BattleAnim_Ingrain
	dw BattleAnim_Superpower
	dw BattleAnim_BrickBreak
	dw BattleAnim_Yawn
	dw BattleAnim_ArmThrust
	dw BattleAnim_BlazeKick
	dw BattleAnim_IceBall
	dw BattleAnim_PoisonFang
	dw BattleAnim_CrushClaw
	dw BattleAnim_MeteorMash
	dw BattleAnim_Aromatherapy
	dw BattleAnim_AirCutter
	dw BattleAnim_Overheat
	dw BattleAnim_RockTomb
	dw BattleAnim_SilverWind
	dw BattleAnim_SignalBeam
	dw BattleAnim_ShadowPunch
	dw BattleAnim_Extrasensory
	dw BattleAnim_SkyUppercut
	dw BattleAnim_SandTomb
	dw BattleAnim_BulletSeed
	dw BattleAnim_AerialAce
	dw BattleAnim_Block
	dw BattleAnim_Howl
	dw BattleAnim_DragonClaw
	dw BattleAnim_BulkUp
	dw BattleAnim_MudShot
	dw BattleAnim_PoisonTail
	dw BattleAnim_VoltTackle
	dw BattleAnim_MagicalLeaf
	dw BattleAnim_CalmMind
	dw BattleAnim_DragonDance
	dw BattleAnim_RockBlast
	dw BattleAnim_ShockWave
	dw BattleAnim_WaterPulse
	dw BattleAnim_Pluck
	dw BattleAnim_SuckerPunch
	dw BattleAnim_ForcePalm
	dw BattleAnim_PoisonJab
	dw BattleAnim_NightSlash
	dw BattleAnim_XScissor
	dw BattleAnim_DrainPunch
	dw BattleAnim_EnergyBall
	dw BattleAnim_BulletPunch
	dw BattleAnim_ShadowClaw
	dw BattleAnim_ThunderFang
	dw BattleAnim_IceFang
	dw BattleAnim_FireFang
	dw BattleAnim_MudBomb
	dw BattleAnim_LavaPlume
	dw BattleAnim_StoneEdge
	dw BattleAnim_BugBite
	dw BattleAnim_SludgeWave
	dw BattleAnim_Hex
	dw BattleAnim_WildCharge
	dw BattleAnim_DrillRun
	dw BattleAnim_IcicleCrash
	assert_table_length NUM_ATTACKS + 1
	dw BattleAnim_SweetScent2

BattleAnim_Dummy:
BattleAnim_MirrorMove:
	anim_ret

BattleAnim_SweetScent2:
	anim_2gfx BATTLE_ANIM_GFX_FLOWER, BATTLE_ANIM_GFX_MISC
	anim_obj BATTLE_ANIM_OBJ_FLOWER, 64, 96, $2
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLOWER, 64, 80, $2
	anim_wait 64
	anim_objparams BATTLE_ANIM_OBJ_COTTON, 136, 40, 3, $15, $2a, $3f
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_wait 128
	anim_ret

BattleAnim_ThrowPokeBall:
	anim_if_param_equal NO_ITEM, .TheTrainerBlockedTheBall
	anim_if_param_equal MASTER_BALL, .MasterBall
	anim_if_param_equal ULTRA_BALL, .UltraBall
	anim_if_param_equal GREAT_BALL, .GreatBall
	; any other ball
	anim_2gfx BATTLE_ANIM_GFX_POKE_BALL, BATTLE_ANIM_GFX_SMOKE
	anim_sound 6, 2, SFX_THROW_BALL
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL, 68, 92, $40
	anim_wait 36
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL, 136, 65, $0
	anim_setobj $2, $7
	anim_wait 16
	anim_sound 0, 1, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 136, 64, $10
	anim_wait 16
	anim_jump .Shake

.TheTrainerBlockedTheBall:
	anim_2gfx BATTLE_ANIM_GFX_POKE_BALL, BATTLE_ANIM_GFX_HIT
	anim_sound 6, 2, SFX_THROW_BALL
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL_BLOCKED, 64, 92, $20
	anim_wait 20
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 112, 40, $0
	anim_wait 32
	anim_ret

.UltraBall:
	anim_2gfx BATTLE_ANIM_GFX_POKE_BALL, BATTLE_ANIM_GFX_SMOKE
	anim_sound 6, 2, SFX_THROW_BALL
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL, 68, 92, $40
	anim_wait 36
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL, 136, 65, $0
	anim_setobj $2, $7
	anim_wait 16
	anim_sound 0, 1, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 136, 64, $10
	anim_wait 16
	anim_jump .Shake

.GreatBall:
	anim_2gfx BATTLE_ANIM_GFX_POKE_BALL, BATTLE_ANIM_GFX_SMOKE
	anim_sound 6, 2, SFX_THROW_BALL
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL, 68, 92, $40
	anim_wait 36
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL, 136, 65, $0
	anim_setobj $2, $7
	anim_wait 16
	anim_sound 0, 1, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 136, 64, $10
	anim_wait 16
	anim_jump .Shake

.MasterBall:
	anim_3gfx BATTLE_ANIM_GFX_POKE_BALL, BATTLE_ANIM_GFX_SMOKE, BATTLE_ANIM_GFX_SPEED
	anim_sound 6, 2, SFX_THROW_BALL
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL, 64, 92, $20
	anim_wait 36
	anim_obj BATTLE_ANIM_OBJ_POKE_BALL, 136, 65, $0
	anim_setobj $2, $7
	anim_wait 16
	anim_sound 0, 1, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 136, 64, $10
	anim_wait 24
	anim_sound 0, 1, SFX_MASTER_BALL
	anim_objparams BATTLE_ANIM_OBJ_MASTER_BALL_SPARKLE, 136, 56, 8, $30, $31, $32, $33, $34, $35, $36, $37
	anim_wait 64
.Shake:
	anim_bgeffect BATTLE_BG_EFFECT_RETURN_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 8
	anim_incobj 2
	anim_wait 16
	anim_sound 0, 1, SFX_CHANGE_DEX_MODE
	anim_incobj 1
	anim_wait 32
	anim_sound 0, 1, SFX_BALL_BOUNCE
	anim_wait 104
	anim_setvar $0
.Loop:
	anim_wait 48
	anim_checkpokeball
	anim_if_var_equal $1, .Click
	anim_if_var_equal $2, .BreakFree
	anim_incobj 1
	anim_sound 0, 1, SFX_BALL_WOBBLE
	anim_jump .Loop

.Click:
	anim_keepsprites
	anim_ret

.BreakFree:
	anim_setobj $1, $b
	anim_sound 0, 1, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 136, 64, $10
	anim_wait 2
	anim_bgeffect BATTLE_BG_EFFECT_ENTER_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 32
	anim_ret

BattleAnim_SendOutMon:
	anim_if_param_equal $0, .Normal
	anim_if_param_equal $1, .Shiny
	anim_if_param_equal $2, .Unknown
	anim_1gfx BATTLE_ANIM_GFX_SMOKE
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_BETA_SEND_OUT_MON2, $0, BG_EFFECT_USER, $0
	anim_sound 0, 0, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BETA_BALL_POOF, 48, 96, $0
	anim_bgeffect BATTLE_BG_EFFECT_ENTER_MON, $0, BG_EFFECT_USER, $0
	anim_wait 132
	anim_call BattleAnim_ShowMon_0
	anim_ret

.Unknown:
	anim_1gfx BATTLE_ANIM_GFX_SMOKE
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_BETA_SEND_OUT_MON1, $0, BG_EFFECT_USER, $0
	anim_wait 1
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 0, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BETA_BALL_POOF, 48, 96, $0
	anim_incbgeffect BATTLE_BG_EFFECT_BETA_SEND_OUT_MON1
	anim_wait 96
	anim_incbgeffect BATTLE_BG_EFFECT_BETA_SEND_OUT_MON1
	anim_call BattleAnim_ShowMon_0
	anim_ret

.Shiny:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $3
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SHINY, 48, 96, $0
	anim_wait 4
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SHINY, 48, 96, $8
	anim_wait 4
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SHINY, 48, 96, $10
	anim_wait 4
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SHINY, 48, 96, $18
	anim_wait 4
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SHINY, 48, 96, $20
	anim_wait 4
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SHINY, 48, 96, $28
	anim_wait 4
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SHINY, 48, 96, $30
	anim_wait 4
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SHINY, 48, 96, $38
	anim_wait 32
	anim_ret

.Normal:
	anim_1gfx BATTLE_ANIM_GFX_SMOKE
	anim_sound 0, 0, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 44, 96, $0
	anim_wait 4
	anim_bgeffect BATTLE_BG_EFFECT_ENTER_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_ret

BattleAnim_ReturnMon:
	anim_sound 0, 0, SFX_BALL_POOF
BattleAnimSub_Return:
	anim_bgeffect BATTLE_BG_EFFECT_RETURN_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_ret

BattleAnim_Confused:
	anim_1gfx BATTLE_ANIM_GFX_STATUS
	anim_sound 0, 0, SFX_KINESIS
	anim_objparams BATTLE_ANIM_OBJ_CHICK, 44, 56, 3, $15, $aa, $bf
	anim_wait 96
	anim_ret

BattleAnim_Slp:
	anim_1gfx BATTLE_ANIM_GFX_STATUS
	anim_sound 0, 0, SFX_TAIL_WHIP
.loop
	anim_obj BATTLE_ANIM_OBJ_ASLEEP, 64, 80, $0
	anim_wait 40
	anim_loop 3, .loop
	anim_wait 32
	anim_ret

BattleAnim_Brn:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
.loop
	anim_sound 0, 0, SFX_BURN
	anim_obj BATTLE_ANIM_OBJ_BURNED, 56, 88, $10
	anim_wait 4
	anim_loop 3, .loop
	anim_wait 16
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnim_Psn:
	anim_1gfx BATTLE_ANIM_GFX_POISON
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_sound 0, 0, SFX_POISON
	anim_obj BATTLE_ANIM_OBJ_SKULL, 64, 56, $0
	anim_wait 8
	anim_sound 0, 0, SFX_POISON
	anim_obj BATTLE_ANIM_OBJ_SKULL, 48, 56, $0
	anim_wait 16
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_Psn_Target:
	anim_1gfx BATTLE_ANIM_GFX_POISON
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_sound 0, 0, SFX_POISON
	anim_obj BATTLE_ANIM_OBJ_SKULL, 136, 24, $0
	anim_wait 8
	anim_sound 0, 0, SFX_POISON
	anim_obj BATTLE_ANIM_OBJ_SKULL, 120, 24, $0
	anim_wait 16
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_Sap:
	anim_1gfx BATTLE_ANIM_GFX_CHARGE
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 128, 48, $2
	anim_wait 6
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 136, 64, $3
	anim_wait 6
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 136, 32, $4
	anim_wait 16
	anim_ret

BattleAnim_Frz:
	anim_1gfx BATTLE_ANIM_GFX_ICE
	anim_obj BATTLE_ANIM_OBJ_FROZEN, 44, 110, $0
	anim_sound 0, 0, SFX_SHINE
	anim_wait 16
	anim_sound 0, 0, SFX_SHINE
	anim_wait 16
	anim_ret

BattleAnim_Par:
	anim_1gfx BATTLE_ANIM_GFX_STATUS
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_sound 0, 0, SFX_THUNDERSHOCK
	anim_obj BATTLE_ANIM_OBJ_PARALYZED, 20, 88, $42
	anim_obj BATTLE_ANIM_OBJ_PARALYZED, 76, 88, $c2
	anim_wait 128
	anim_ret

BattleAnim_InLove:
	anim_1gfx BATTLE_ANIM_GFX_OBJECTS
	anim_sound 0, 0, SFX_LICK
	anim_obj BATTLE_ANIM_OBJ_HEART, 64, 76, $0
	anim_wait 32
	anim_sound 0, 0, SFX_LICK
	anim_obj BATTLE_ANIM_OBJ_HEART, 36, 72, $0
	anim_wait 32
	anim_ret

BattleAnim_InSandstorm:
	anim_1gfx BATTLE_ANIM_GFX_POWDER
	anim_call BattleAnimSub_SandstormStart
.loop
	anim_sound 0, 1, SFX_MENU
	anim_wait 8
	anim_loop 6, .loop
	anim_wait 8
	anim_ret

BattleAnim_InHail:
	anim_call BattleAnimSub_HailWeather
.loop
	anim_sound 0, 1, SFX_SHINE
	anim_wait 8
	anim_loop 6, .loop
	anim_wait 8
	anim_ret

BattleAnim_InNightmare:
	anim_1gfx BATTLE_ANIM_GFX_ANGELS
	anim_sound 0, 0, SFX_BUBBLEBEAM
	anim_obj BATTLE_ANIM_OBJ_IN_NIGHTMARE, 68, 80, $0
	anim_wait 40
	anim_ret

BattleAnim_InWhirlpool:
	anim_1gfx BATTLE_ANIM_GFX_WIND
	anim_bgeffect BATTLE_BG_EFFECT_WHIRLPOOL, $0, $0, $0
	anim_sound 0, 1, SFX_SURF
.loop
	anim_obj BATTLE_ANIM_OBJ_GUST, 132, 72, $0
	anim_wait 6
	anim_loop 6, .loop
	anim_incbgeffect BATTLE_BG_EFFECT_WHIRLPOOL
	anim_wait 1
	anim_ret

BattleAnim_HitConfusion:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_POUND
	anim_obj BATTLE_ANIM_OBJ_HIT, 44, 96, $0
	anim_wait 16
	anim_ret

BattleAnim_Miss:
	anim_ret

BattleAnim_EnemyDamage:
.loop
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 5
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 5
	anim_loop 3, .loop
	anim_ret

BattleAnim_StatDown:
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK_REPEATING, $0, BG_EFFECT_TARGET, $40
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK_REPEATING
	anim_wait 8
	anim_ret

BattleAnim_StatUp:
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING, $0, BG_EFFECT_USER, $40
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING
	anim_wait 8
	anim_ret

BattleAnim_PlayerDamage:
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_Y, $20, $2, $20
	anim_wait 40
	anim_ret

BattleAnim_Wobble:
	anim_bgeffect BATTLE_BG_EFFECT_WOBBLE_SCREEN, $0, $0, $0
	anim_wait 40
	anim_ret

BattleAnim_Shake:
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $40
	anim_wait 40
	anim_ret

BattleAnim_Pound:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_POUND
	anim_obj BATTLE_ANIM_OBJ_PALM, 136, 56, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_KarateChop:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_KARATE_CHOP
	anim_obj BATTLE_ANIM_OBJ_PALM, 136, 40, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 40, $0
	anim_wait 6
	anim_sound 0, 1, SFX_KARATE_CHOP
	anim_obj BATTLE_ANIM_OBJ_PALM, 136, 44, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 44, $0
	anim_wait 6
	anim_sound 0, 1, SFX_KARATE_CHOP
	anim_obj BATTLE_ANIM_OBJ_PALM, 136, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_wait 16
	anim_ret

BattleAnim_Doubleslap:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_if_param_equal $1, .alternate
	anim_sound 0, 1, SFX_DOUBLESLAP
	anim_obj BATTLE_ANIM_OBJ_PALM, 144, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_wait 8
	anim_ret

.alternate:
	anim_sound 0, 1, SFX_DOUBLESLAP
	anim_obj BATTLE_ANIM_OBJ_PALM, 120, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 48, $0
	anim_wait 8
	anim_ret

BattleAnim_CometPunch:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_if_param_equal $1, .alternate
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 144, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_wait 8
	anim_ret

.alternate:
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 120, 64, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 64, $0
	anim_wait 8
	anim_ret

BattleAnim_MegaPunch:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $2, $0
	anim_wait 48
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $3
	anim_call BattleAnimSub_MegaPunchHits
	anim_ret

BattleAnim_Stomp:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_STOMP
	anim_obj BATTLE_ANIM_OBJ_KICK, 136, 40, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 40, $0
	anim_wait 6
	anim_sound 0, 1, SFX_STOMP
	anim_obj BATTLE_ANIM_OBJ_KICK, 136, 44, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 44, $0
	anim_wait 6
	anim_sound 0, 1, SFX_STOMP
	anim_obj BATTLE_ANIM_OBJ_KICK, 136, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_wait 16
	anim_ret

BattleAnim_DoubleKick:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_if_param_equal $1, .alternate
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 144, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_wait 8
	anim_ret

.alternate:
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 120, 64, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 64, $0
	anim_wait 8
	anim_ret

BattleAnim_JumpKick:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_if_param_equal $1, .alternate
	anim_sound 0, 1, SFX_JUMP_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 112, 72, $0
	anim_obj BATTLE_ANIM_OBJ_KICK, 100, 60, $0
	anim_setobj $1, $2
	anim_setobj $2, $2
	anim_wait 24
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT, 136, 48, $0
	anim_wait 16
	anim_ret

.alternate:
	anim_wait 8
	anim_sound 0, 0, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT, 44, 88, $0
	anim_wait 16
	anim_ret

BattleAnim_HiJumpKick:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $2, $0
	anim_if_param_equal $1, .alternate
	anim_wait 32
	anim_sound 0, 1, SFX_JUMP_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 112, 72, $0
	anim_setobj $1, $2
	anim_wait 16
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT, 136, 48, $0
	anim_wait 16
	anim_ret

.alternate:
	anim_wait 16
	anim_sound 0, 0, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT, 44, 88, $0
	anim_wait 16
	anim_ret

BattleAnim_RollingKick:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 112, 56, $0
	anim_setobj $1, $3
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_wait 16
	anim_ret

BattleAnim_MegaKick:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $2, $0
	anim_wait 67
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $3
.loop
	anim_sound 0, 1, SFX_MEGA_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 136, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_KICK, 136, 56, $0
	anim_wait 6
	anim_loop 3, .loop
	anim_ret

BattleAnim_HyperFang:
	anim_2gfx BATTLE_ANIM_GFX_HYPER_FANG, BATTLE_ANIM_GFX_HIT
	anim_hyperfangpal BATTLE_ANIM_HYPER_FANG_PAL_LOAD
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HYPER_FANG, 136, 56, $0
	anim_wait 10
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $1, $0
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_obj BATTLE_ANIM_OBJ_HIT, 136, 56, $0
	anim_wait 28
	anim_hyperfangpal BATTLE_ANIM_HYPER_FANG_PAL_RESTORE
	anim_ret

BattleAnim_SuperFang:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $2, $0
	anim_wait 48
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $3
.loop
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_FANG, 136, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_FANG, 136, 56, $0
	anim_wait 6
	anim_loop 3, .loop
	anim_ret

BattleAnim_Ember:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
	anim_sound 6, 2, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_EMBER_PROJECTILE, 64, 96, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_EMBER_PROJECTILE, 64, 96, $1
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_EMBER_PROJECTILE, 64, 96, $2
	anim_wait 16
	anim_sound 0, 1, SFX_EMBER
	anim_call BattleAnimSub_EmberFireHit
	anim_call BattleAnimSub_EmberFireHit
	anim_call BattleAnimSub_EmberFireHit
	anim_wait 24
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnimSub_EmberFireHit:
	anim_obj BATTLE_ANIM_OBJ_EMBER_FLARE, 136, 68, $80
	anim_wait 4
	anim_ret

BattleAnim_FirePunch:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
	anim_obj BATTLE_ANIM_OBJ_PUNCH_SHAKE, 136, 56, $43
	anim_wait 3
	anim_call BattleAnimSub_Fire
	anim_wait 16
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnim_FireSpin:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
.loop
	anim_call BattleAnimSub_FireSpinOpener
	anim_loop 2, .loop
	anim_wait 96
.loop2
	anim_sound 0, 0, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FLAME_WHEEL, 132, 64, $0
	anim_wait 6
	anim_loop 8, .loop2
	anim_wait 120
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnim_DragonRage:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_LOAD
.loop
	anim_sound 6, 2, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_DRAGON_RAGE, 64, 92, $0
	anim_wait 3
	anim_loop 16, .loop
	anim_wait 64
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_RESTORE
	anim_ret

BattleAnim_Flamethrower:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
	anim_call BattleAnimSub_FlamethrowerCore
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnimSub_FlamethrowerCore:
	anim_sound 6, 2, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FLAMETHROWER, 64, 92, $3
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLAMETHROWER, 75, 86, $5
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLAMETHROWER, 85, 81, $7
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLAMETHROWER, 96, 76, $9
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLAMETHROWER, 106, 71, $b
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLAMETHROWER, 116, 66, $c
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLAMETHROWER, 126, 61, $a
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLAMETHROWER, 136, 56, $8
	anim_wait 16
.loop
	anim_sound 6, 2, SFX_EMBER
	anim_wait 16
	anim_loop 6, .loop
	anim_wait 16
	anim_clearobjs
	anim_obj BATTLE_ANIM_OBJ_EMBER_AFTEREFFECT, 120, 72, $2
	anim_wait 1
	anim_obj BATTLE_ANIM_OBJ_EMBER_AFTEREFFECT, 136, 72, $2
	anim_wait 1
	anim_obj BATTLE_ANIM_OBJ_EMBER_AFTEREFFECT, 152, 72, $2
	anim_wait 24
	anim_ret

BattleAnim_FireBlast:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
.loop
	anim_sound 6, 2, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FIRE_BLAST_ORBIT, 48, 88, $00
	anim_wait 3
	anim_loop 8, .loop
	anim_wait 32
	anim_sound 0, 1, SFX_EMBER
	anim_incobjrange 1, 8
	anim_wait 24
	anim_sound 0, 1, SFX_EMBER
.eruption_loop
	anim_call BattleAnimSub_FireBlastEruptionSet
	anim_wait 11
	anim_loop 5, .eruption_loop
	anim_wait 9
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnimSub_FireBlastEruptionSet:
	anim_objparams BATTLE_ANIM_OBJ_FIRE_BLAST_ERUPTION, 136, 56, 5, $81, $82, $83, $84, $85
	anim_ret

BattleAnim_IcePunch:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_ICE
	anim_obj BATTLE_ANIM_OBJ_PUNCH_SHAKE, 136, 56, $43
	anim_call BattleAnimSub_Ice
	anim_wait 32
	anim_ret

BattleAnim_IceBeam:
	anim_1gfx BATTLE_ANIM_GFX_ICE
.loop
	anim_sound 6, 2, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_ICE_BEAM, 64, 92, $4
	anim_wait 4
	anim_loop 5, .loop
	anim_obj BATTLE_ANIM_OBJ_ICE_BUILDUP, 136, 74, $10
.loop2
	anim_sound 6, 2, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_ICE_BEAM, 64, 92, $4
	anim_wait 4
	anim_loop 15, .loop2
	anim_wait 48
	anim_sound 0, 1, SFX_SHINE
	anim_wait 8
	anim_sound 0, 1, SFX_SHINE
	anim_wait 8
	anim_ret

BattleAnim_Blizzard:
	anim_1gfx BATTLE_ANIM_GFX_ICE
.loop
	anim_call BattleAnimSub_BlizzardSweep
	anim_loop 3, .loop
	anim_bgeffect BATTLE_BG_EFFECT_WHITE_HUES, $0, $8, $0
	anim_wait 32
	anim_obj BATTLE_ANIM_OBJ_ICE_BUILDUP, 136, 74, $10
	anim_wait 128
	anim_sound 0, 1, SFX_SHINE
	anim_wait 8
	anim_sound 0, 1, SFX_SHINE
	anim_wait 24
	anim_ret

BattleAnim_Bubble:
	anim_1gfx BATTLE_ANIM_GFX_BUBBLE
	anim_sound 32, 2, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_BUBBLE, 64, 92, $c1
	anim_wait 6
	anim_sound 32, 2, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_BUBBLE, 64, 92, $e1
	anim_wait 6
	anim_sound 32, 2, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_BUBBLE, 64, 92, $d1
	anim_wait 160
	anim_ret

BattleAnim_Bubblebeam:
	anim_1gfx BATTLE_ANIM_GFX_BUBBLE
.loop
	anim_sound 16, 2, SFX_BUBBLEBEAM
	anim_obj BATTLE_ANIM_OBJ_BUBBLE, 64, 92, $92
	anim_wait 6
	anim_sound 16, 2, SFX_BUBBLEBEAM
	anim_obj BATTLE_ANIM_OBJ_BUBBLE, 64, 92, $b3
	anim_wait 6
	anim_sound 16, 2, SFX_BUBBLEBEAM
	anim_obj BATTLE_ANIM_OBJ_BUBBLE, 64, 92, $f4
	anim_wait 8
	anim_loop 3, .loop
	anim_wait 64
	anim_clearobjs
	anim_bgeffect BATTLE_BG_EFFECT_START_WATER, $0, BG_EFFECT_TARGET, $0
	anim_wait 1
	anim_call BattleAnim_UserObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $1c, $0, $0
	anim_wait 19
	anim_call BattleAnim_ShowMon_1
	anim_bgeffect BATTLE_BG_EFFECT_END_WATER, $0, $0, $0
	anim_wait 8
	anim_ret

BattleAnim_WaterGun:
	anim_bgeffect BATTLE_BG_EFFECT_START_WATER, $0, BG_EFFECT_TARGET, $0
	anim_1gfx BATTLE_ANIM_GFX_WATER
	anim_call BattleAnim_UserObj_2Row
	anim_sound 16, 2, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_WATER_GUN, 64, 88, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_WATER_GUN, 64, 76, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_WATER_GUN, 64, 82, $0
	anim_wait 24
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $1c, $0, $0
	anim_wait 8
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $8, $0, $0
	anim_wait 8
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $30, $0, $0
	anim_wait 32
	anim_call BattleAnim_ShowMon_1
	anim_bgeffect BATTLE_BG_EFFECT_END_WATER, $0, $0, $0
	anim_wait 16
	anim_ret

BattleAnim_HydroPump:
	anim_bgeffect BATTLE_BG_EFFECT_START_WATER, $0, BG_EFFECT_TARGET, $0
	anim_1gfx BATTLE_ANIM_GFX_WATER_COLUMN
	anim_watercolumnpal BATTLE_ANIM_WATER_COLUMN_PAL_LOAD
	anim_sound 0, 1, SFX_HYDRO_PUMP
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP_COLUMN, 108, 72, $0
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $1c, $0, $0
	anim_wait 14
	anim_sound 0, 1, SFX_HYDRO_PUMP
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP_COLUMN, 120, 72, $0
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $8, $0, $0
	anim_wait 14
	anim_sound 0, 1, SFX_HYDRO_PUMP
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP_COLUMN, 132, 72, $0
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $30, $0, $0
	anim_wait 14
	anim_sound 0, 1, SFX_HYDRO_PUMP
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP_COLUMN_SLOW, 144, 72, $0
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $1c, $0, $0
	anim_wait 14
	anim_sound 0, 1, SFX_HYDRO_PUMP
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP_COLUMN_SLOW, 156, 72, $0
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $8, $0, $0
	anim_wait 14
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $30, $0, $0
	anim_wait 14
	anim_bgeffect BATTLE_BG_EFFECT_WATER, $1c, $0, $0
	anim_wait 26
	anim_watercolumnpal BATTLE_ANIM_WATER_COLUMN_PAL_RESTORE
	anim_bgeffect BATTLE_BG_EFFECT_END_WATER, $0, $0, $0
	anim_wait 16
	anim_ret

BattleAnim_Surf:
	anim_1gfx BATTLE_ANIM_GFX_BUBBLE
	anim_bgeffect BATTLE_BG_EFFECT_SURF, $0, $0, $0
	anim_obj BATTLE_ANIM_OBJ_SURF, 88, 104, $8
.loop
	anim_sound 0, 1, SFX_SURF
	anim_wait 32
	anim_loop 4, .loop
	anim_incobj 1
	anim_wait 56
	anim_ret

BattleAnim_VineWhip:
	anim_2gfx BATTLE_ANIM_GFX_VINE_WHIP, BATTLE_ANIM_GFX_HIT
	anim_grasspal BATTLE_ANIM_GRASS_PAL_LOAD
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_VINE_WHIP
	anim_obj BATTLE_ANIM_OBJ_VINE_WHIP1, 112, 48, $0
	anim_wait 20
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX_GREEN, 128, 48, $0
	anim_wait 18
	anim_grasspal BATTLE_ANIM_GRASS_PAL_RESTORE
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_LeechSeed:
	anim_1gfx BATTLE_ANIM_GFX_PLANT
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_obj BATTLE_ANIM_OBJ_LEECH_SEED, 48, 80, $20
	anim_wait 8
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_obj BATTLE_ANIM_OBJ_LEECH_SEED, 48, 80, $30
	anim_wait 8
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_obj BATTLE_ANIM_OBJ_LEECH_SEED, 48, 80, $28
	anim_wait 32
	anim_sound 0, 1, SFX_CHARGE
	anim_wait 128
	anim_ret

BattleAnim_RazorLeaf:
	anim_2gfx BATTLE_ANIM_GFX_PLANT, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_VINE_WHIP
	anim_objparams BATTLE_ANIM_OBJ_RAZOR_LEAF, 48, 80, 6, $28, $5c, $10, $e8, $9c, $d0
	anim_wait 6
	anim_objparams BATTLE_ANIM_OBJ_RAZOR_LEAF, 48, 80, 4, $1c, $50, $dc, $90
	anim_wait 80
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 3
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 5
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 7
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 9
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 1
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 2
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 4
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 6
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 8
	anim_wait 2
	anim_sound 16, 2, SFX_VINE_WHIP
	anim_incobj 10
	anim_wait 64
	anim_ret

BattleAnim_Solarbeam:
	anim_if_param_equal $0, .FireSolarBeam
	; charge turn
	anim_1gfx BATTLE_ANIM_GFX_CHARGE
	anim_sound 0, 0, SFX_CHARGE
	anim_obj BATTLE_ANIM_OBJ_ABSORB_CENTER, 48, 84, $0
	anim_objparams BATTLE_ANIM_OBJ_SOLAR_BEAM_CHARGE, 48, 84, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 104
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_WHITE, $0, $4, $2
	anim_wait 64
	anim_ret

.FireSolarBeam
	anim_1gfx BATTLE_ANIM_GFX_BEAM
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_call BattleAnimSub_Beam
	anim_wait 48
	anim_ret

BattleAnim_Thunderpunch:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_THUNDER
	anim_thunderpal BATTLE_ANIM_THUNDER_PAL_LOAD
	anim_obj BATTLE_ANIM_OBJ_PUNCH_SHAKE, 136, 56, $43
	anim_wait 10
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $1, $6, $4
	anim_sound 0, 1, SFX_THUNDER
	anim_obj BATTLE_ANIM_OBJ_THUNDER_STRIKE_CONTROLLER, 136, 0, $0
	anim_wait 51
	anim_thunderpal BATTLE_ANIM_THUNDER_PAL_RESTORE
	anim_wait 64
	anim_ret

BattleAnim_Thundershock:
	anim_2gfx BATTLE_ANIM_GFX_THUNDERSHOCK, BATTLE_ANIM_GFX_ELECTRICITY_EFFECT
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $1
	anim_sound 0, 1, SFX_THUNDER
	anim_obj BATTLE_ANIM_OBJ_THUNDERSHOCK_STRIKE, 136, 68, $0
	anim_wait 60
	anim_sound 0, 1, SFX_THUNDERSHOCK_SHORT
	anim_call BattleAnimSub_ElectricityEffect
	anim_ret

BattleAnimSub_ElectricityEffect:
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 141, 56, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 131, 66, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 151, 76, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 121, 46, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 161, 56, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 128, 64, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 138, 48, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 116, 71, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 141, 56, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 131, 66, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 121, 46, $0
	anim_wait 25
	anim_ret

BattleAnimSub_ElectricityEffectUser:
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 48, 92, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 38, 98, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 58, 100, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 28, 86, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 68, 92, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 35, 96, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 55, 84, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 25, 100, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 48, 92, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 38, 98, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 28, 86, $0
	anim_wait 25
	anim_ret

BattleAnim_Thunderbolt:
	anim_4gfx BATTLE_ANIM_GFX_THUNDERSHOCK, BATTLE_ANIM_GFX_THUNDERBOLT, BATTLE_ANIM_GFX_THUNDERBOLT_AFTEREFFECT, BATTLE_ANIM_GFX_ELECTRICITY_EFFECT
	anim_thunderboltpal BATTLE_ANIM_THUNDERBOLT_PAL_LOAD
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_sound 0, 1, SFX_THUNDER
	anim_obj BATTLE_ANIM_OBJ_THUNDERSHOCK_STRIKE, 160, 68, $0
	anim_wait 7
	anim_obj BATTLE_ANIM_OBJ_THUNDERSHOCK_STRIKE, 112, 68, $0
	anim_wait 7
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_obj BATTLE_ANIM_OBJ_THUNDERBOLT_STRIKE, 136, 68, $0
	anim_wait 60
	anim_call BattleAnimSub_ThunderboltAftereffect
	anim_call BattleAnimSub_ElectricityEffect
	anim_thunderboltpal BATTLE_ANIM_THUNDERBOLT_PAL_RESTORE
	anim_wait 4
	anim_ret

BattleAnimSub_ThunderboltAftereffect:
	anim_sound 0, 1, SFX_THUNDERSHOCK_LONG
	anim_obj BATTLE_ANIM_OBJ_THUNDERBOLT_AFTEREFFECT, 136, 56, $0
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 160, 56, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 148, 40, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 124, 40, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 112, 56, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 124, 72, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 148, 72, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 156, 44, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 136, 38, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 116, 44, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 116, 68, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 136, 74, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 156, 68, $0
	anim_wait 12
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 160, 64, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 144, 38, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 120, 48, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 112, 64, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 132, 74, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 152, 48, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 156, 44, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 136, 38, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 116, 44, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT, 116, 68, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_XFLIP, 136, 74, $0
	anim_obj BATTLE_ANIM_OBJ_ELECTRICITY_EFFECT_YFLIP, 156, 68, $0
	anim_wait 30
	anim_ret

BattleAnim_ThunderWave:
	anim_1gfx BATTLE_ANIM_GFX_LIGHTNING
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $3
	anim_sound 0, 1, SFX_THUNDERSHOCK
	anim_obj BATTLE_ANIM_OBJ_THUNDER_WAVE, 136, 56, $0
	anim_wait 20
	anim_bgp $1b
	anim_incobj 1
	anim_wait 96
	anim_ret

BattleAnim_Thunder:
	anim_1gfx BATTLE_ANIM_GFX_THUNDER
	anim_thunderpal BATTLE_ANIM_THUNDER_PAL_LOAD
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $1, $6, $4
	anim_sound 0, 1, SFX_THUNDER
	anim_obj BATTLE_ANIM_OBJ_THUNDER_STRIKE_CONTROLLER, 152, 0, $0
	anim_wait 42
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $1, $6, $4
	anim_sound 0, 1, SFX_THUNDER
	anim_obj BATTLE_ANIM_OBJ_THUNDER_STRIKE_CONTROLLER, 120, 0, $0
	anim_wait 42
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $1, $6, $4
	anim_sound 0, 1, SFX_THUNDER
	anim_obj BATTLE_ANIM_OBJ_THUNDER_STRIKE_CONTROLLER, 152, 0, $0
	anim_wait 54
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $1, $6, $4
	anim_sound 0, 1, SFX_THUNDER
	anim_obj BATTLE_ANIM_OBJ_THUNDER_STRIKE_CONTROLLER, 136, 0, $0
	anim_wait 42
	anim_thunderpal BATTLE_ANIM_THUNDER_PAL_RESTORE
	anim_wait 8
	anim_ret

BattleAnim_RazorWind:
	anim_if_param_equal $1, BattleAnim_FocusEnergy
	anim_1gfx BATTLE_ANIM_GFX_WHIP
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $1, $0
.loop
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_RAZOR_WIND2, 152, 40, $3
	anim_wait 4
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_RAZOR_WIND2, 136, 56, $3
	anim_wait 4
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_RAZOR_WIND2, 152, 64, $3
	anim_wait 4
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_RAZOR_WIND1, 120, 40, $83
	anim_wait 4
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_RAZOR_WIND1, 120, 64, $83
	anim_wait 4
	anim_loop 3, .loop
	anim_wait 24
	anim_ret

BattleAnim_Gust:
BattleAnim_Sonicboom:
	anim_2gfx BATTLE_ANIM_GFX_WIND, BATTLE_ANIM_GFX_HIT
.loop
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_GUST, 136, 72, $0
	anim_wait 6
	anim_loop 9, .loop
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 64, $18
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 32, $18
	anim_wait 16
	anim_ret

BattleAnim_Selfdestruct:
	anim_1gfx BATTLE_ANIM_GFX_EXPLOSION
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $24
	anim_if_param_equal $1, .loop
	anim_call BattleAnimSub_Explosion2
	anim_wait 16
	anim_ret

.loop
	anim_call BattleAnimSub_Explosion1
	anim_wait 5
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_loop 2, .loop
	anim_wait 16
	anim_ret

BattleAnim_Explosion:
	anim_1gfx BATTLE_ANIM_GFX_EXPLOSION
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $60, $4, $10
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $24
	anim_if_param_equal $1, .loop
	anim_call BattleAnimSub_Explosion2
	anim_wait 16
	anim_ret

.loop
	anim_call BattleAnimSub_Explosion1
	anim_wait 5
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_loop 2, .loop
	anim_wait 16
	anim_ret

BattleAnim_Acid:
	anim_1gfx BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_sound 6, 2, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ACID_BUBBLE, 64, 92, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_ACID_BUBBLE, 64, 92, $1
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_ACID_BUBBLE, 64, 92, $2
	anim_wait 15
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $1, $0
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_ACID_DROPLET, 136, 34, $1a
	anim_wait 10
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_ACID_DROPLET, 110, 32, $1c
	anim_wait 10
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_ACID_DROPLET, 151, 29, $1e
	anim_wait 10
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_ACID_DROPLET, 121, 39, $16
	anim_wait 10
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_ACID_DROPLET, 160, 34, $1a
	anim_wait 32
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_RockThrow:
	anim_1gfx BATTLE_ANIM_GFX_ROCKS
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $60, $1, $0
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 128, 64, $40
	anim_wait 2
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 120, 68, $30
	anim_wait 2
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 152, 68, $30
	anim_wait 2
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 144, 64, $40
	anim_wait 2
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 136, 68, $30
	anim_wait 96
	anim_ret

BattleAnim_RockSlide:
	anim_1gfx BATTLE_ANIM_GFX_ROCKS
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $c0, $1, $0
.loop
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 128, 64, $40
	anim_wait 4
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 120, 68, $30
	anim_wait 4
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 152, 68, $30
	anim_wait 4
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 144, 64, $40
	anim_wait 4
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 136, 68, $30
	anim_wait 16
	anim_loop 4, .loop
	anim_wait 96
	anim_ret

BattleAnim_Sing:
	anim_1gfx BATTLE_ANIM_GFX_NOISE
	anim_sound 16, 2, SFX_SING
.loop
	anim_obj BATTLE_ANIM_OBJ_SING, 64, 92, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SING, 64, 92, $1
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SING, 64, 92, $2
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SING, 64, 92, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SING, 64, 92, $2
	anim_wait 8
	anim_loop 4, .loop
	anim_wait 64
	anim_ret

BattleAnim_Poisonpowder:
	anim_1gfx BATTLE_ANIM_GFX_POISON_POWDER
	anim_poisonpal BATTLE_ANIM_POISON_POWDER_PAL_LOAD
	anim_call BattleAnimSub_PowderController
	anim_poisonpal BATTLE_ANIM_POISON_POWDER_PAL_RESTORE
	anim_ret

BattleAnim_StunSpore:
	anim_1gfx BATTLE_ANIM_GFX_POISON_POWDER
	anim_poisonpal BATTLE_ANIM_STUN_SPORE_PAL_LOAD
	anim_call BattleAnimSub_PowderController
	anim_poisonpal BATTLE_ANIM_STUN_SPORE_PAL_RESTORE
	anim_ret

BattleAnim_SleepPowder:
	anim_1gfx BATTLE_ANIM_GFX_POISON_POWDER
	anim_poisonpal BATTLE_ANIM_SLEEP_POWDER_PAL_LOAD
	anim_call BattleAnimSub_PowderController
	anim_poisonpal BATTLE_ANIM_SLEEP_POWDER_PAL_RESTORE
	anim_ret

BattleAnim_Spore:
	anim_1gfx BATTLE_ANIM_GFX_POISON_POWDER
	anim_poisonpal BATTLE_ANIM_SPORE_PAL_LOAD
	anim_call BattleAnimSub_PowderController
	anim_poisonpal BATTLE_ANIM_SPORE_PAL_RESTORE
	anim_ret

BattleAnimSub_PowderController:
	anim_sound 0, 1, SFX_POWDER
	anim_obj BATTLE_ANIM_OBJ_POISON_POWDER, 0, 0, $0
	; Five repeats after the opening sound produce SFX at frames 10, 20, 30, 40, and 50.
.loop
	anim_wait 10
	anim_sound 0, 1, SFX_POWDER
	anim_loop 5, .loop
	anim_wait 135
	anim_ret

BattleAnim_HyperBeam:
	anim_1gfx BATTLE_ANIM_GFX_BEAM
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $30, $4, $10
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $40
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_call BattleAnimSub_Beam
	anim_wait 48
	anim_ret

BattleAnim_AuroraBeam:
	anim_1gfx BATTLE_ANIM_GFX_AURORA_BEAM
	anim_aurorapal BATTLE_ANIM_AURORA_BEAM_PAL_LOAD
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_sound 0, 0, SFX_BUBBLEBEAM
.loop1
	anim_extobj BATTLE_ANIM_EXT_OBJ_AURORA_BEAM_RING, 64, 92, $0
	anim_wait 4
	anim_sound 0, 1, SFX_BUBBLEBEAM
	anim_loop 8, .loop1
.loop2
	anim_extobj BATTLE_ANIM_EXT_OBJ_AURORA_BEAM_RING, 64, 92, $0
	anim_wait 4
	anim_sound 0, 1, SFX_BUBBLEBEAM
	anim_loop 16, .loop2
	anim_wait 48
	anim_aurorapal BATTLE_ANIM_AURORA_BEAM_PAL_RESTORE
	anim_ret

BattleAnim_Vicegrip:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_sound 0, 1, SFX_VICEGRIP
	anim_obj BATTLE_ANIM_OBJ_CUT_DOWN_LEFT, 152, 40, $0
	anim_obj BATTLE_ANIM_OBJ_CUT_UP_RIGHT, 120, 72, $0
	anim_wait 32
	anim_ret

BattleAnim_Scratch:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_call BattleAnimSub_ScratchDownLeft
	anim_wait 32
	anim_ret

BattleAnim_FurySwipes:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_if_param_equal $1, .alternate
	anim_call BattleAnimSub_ScratchDownLeft
	anim_sound 0, 1, SFX_SCRATCH
	anim_wait 32
	anim_ret

.alternate:
	anim_sound 0, 1, SFX_SCRATCH
	anim_objlist BATTLE_ANIM_OBJ_CUT_DOWN_RIGHT, 3, 120, 48, $0, 124, 44, $0, 128, 40, $0
	anim_sound 0, 1, SFX_SCRATCH
	anim_wait 32
	anim_ret

BattleAnim_Cut:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_sound 0, 1, SFX_CUT
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
	anim_wait 32
	anim_ret

BattleAnim_Slash:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_sound 0, 1, SFX_CUT
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 148, 36, $0
	anim_wait 32
	anim_ret

BattleAnim_Clamp:
	anim_2gfx BATTLE_ANIM_GFX_CUT, BATTLE_ANIM_GFX_HIT
	anim_objparams BATTLE_ANIM_OBJ_CLAMP, 136, 56, 2, $a0, $20
	anim_wait 16
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $18
	anim_wait 32
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 64, $18
	anim_wait 16
	anim_ret

BattleAnim_Bite:
	anim_2gfx BATTLE_ANIM_GFX_CUT, BATTLE_ANIM_GFX_HIT
	anim_call BattleAnimSub_BiteJaws
	anim_wait 8
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $18
	anim_wait 16
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 64, $18
	anim_wait 8
	anim_ret

BattleAnim_Teleport:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TELEPORT, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 3
	anim_incbgeffect BATTLE_BG_EFFECT_TELEPORT
	anim_call BattleAnim_ShowMon_0
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $1, $0
	anim_call BattleAnimSub_WarpAway
	anim_wait 64
	anim_ret

BattleAnim_Fly:
	anim_if_param_equal $1, .turn1
	anim_if_param_equal $2, .miss
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_WING_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 32
.miss:
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_ret

.turn1:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $1, $0
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_call BattleAnimSub_WarpAway
	anim_wait 64
	anim_ret

BattleAnim_DoubleTeam:
	anim_call BattleAnim_TargetObj_2Row
	anim_sound 0, 0, SFX_PSYBEAM
	anim_bgeffect BATTLE_BG_EFFECT_DOUBLE_TEAM, $0, BG_EFFECT_USER, $0
	anim_wait 96
	anim_incbgeffect BATTLE_BG_EFFECT_DOUBLE_TEAM
	anim_wait 24
	anim_incbgeffect BATTLE_BG_EFFECT_DOUBLE_TEAM
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Recover:
	anim_1gfx BATTLE_ANIM_GFX_BUBBLE
	anim_call BattleAnim_TargetObj_1Row
	anim_sound 0, 0, SFX_FULL_HEAL
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING, $0, BG_EFFECT_USER, $40
	anim_objparams BATTLE_ANIM_OBJ_RECOVER, 44, 88, 8, $30, $31, $32, $33, $34, $35, $36, $37
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Absorb:
	anim_1gfx BATTLE_ANIM_GFX_CHARGE
	anim_obj BATTLE_ANIM_OBJ_ABSORB_CENTER, 44, 88, $0
.loop
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 128, 48, $2
	anim_wait 6
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 136, 64, $3
	anim_wait 6
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 136, 32, $4
	anim_wait 6
	anim_loop 5, .loop
	anim_wait 32
	anim_ret

BattleAnim_MegaDrain:
	anim_1gfx BATTLE_ANIM_GFX_CHARGE
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MONS_TO_BLACK_REPEATING, $0, BG_EFFECT_TARGET, $10
	anim_setvar $0
.loop
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 128, 48, $2
	anim_wait 6
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 136, 64, $3
	anim_wait 6
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 136, 32, $4
	anim_wait 6
	anim_incvar
	anim_if_var_equal $7, .done
	anim_if_var_equal $2, .spawn
	anim_jump .loop

.spawn
	anim_obj BATTLE_ANIM_OBJ_ABSORB_CENTER, 44, 88, $0
	anim_jump .loop

.done
	anim_wait 32
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MONS_TO_BLACK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_EggBomb:
	anim_2gfx BATTLE_ANIM_GFX_EGG, BATTLE_ANIM_GFX_EXPLOSION
	anim_sound 0, 0, SFX_SWITCH_POKEMON
	anim_obj BATTLE_ANIM_OBJ_EGG, 44, 104, $1
	anim_wait 128
	anim_wait 96
	anim_incobj 1
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $3
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION2, 128, 64, $0
	anim_wait 8
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION2, 144, 68, $0
	anim_wait 8
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION2, 136, 72, $0
	anim_wait 24
	anim_ret

BattleAnim_Softboiled:
	anim_2gfx BATTLE_ANIM_GFX_EGG, BATTLE_ANIM_GFX_BUBBLE
	anim_call BattleAnim_TargetObj_1Row
	anim_sound 0, 0, SFX_SWITCH_POKEMON
	anim_obj BATTLE_ANIM_OBJ_EGG, 44, 104, $6
	anim_wait 128
	anim_incobj 2
	anim_obj BATTLE_ANIM_OBJ_EGG, 76, 104, $b
	anim_wait 16
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING, $0, BG_EFFECT_USER, $40
	anim_sound 0, 0, SFX_METRONOME
.loop
	anim_obj BATTLE_ANIM_OBJ_RECOVER, 44, 88, $20
	anim_wait 8
	anim_loop 8, .loop
	anim_wait 128
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_FocusEnergy:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT, $0, BG_EFFECT_USER, $40
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
.loop
	anim_call BattleAnimSub_FocusEnergyBurst
	anim_loop 3, .loop
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Bide:
	anim_if_param_equal $0, BattleAnim_MegaPunch
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_sound 0, 0, SFX_ESCAPE_ROPE
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING, $0, BG_EFFECT_USER, $20
	anim_wait 72
	anim_incbgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Bind:
	anim_1gfx BATTLE_ANIM_GFX_ROPE
	anim_sound 0, 1, SFX_BIND
	anim_obj BATTLE_ANIM_OBJ_BIND1, 132, 64, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_BIND2, 132, 56, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_BIND1, 132, 48, $0
	anim_wait 64
	anim_sound 0, 1, SFX_BIND
	anim_incobjrange 1, 3
	anim_wait 96
	anim_ret

BattleAnim_Wrap:
	anim_1gfx BATTLE_ANIM_GFX_ROPE
	anim_sound 0, 1, SFX_BIND
	anim_obj BATTLE_ANIM_OBJ_BIND1, 132, 64, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_BIND1, 132, 56, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_BIND1, 132, 48, $0
	anim_wait 64
	anim_sound 0, 1, SFX_BIND
	anim_incobjrange 1, 3
	anim_wait 96
	anim_ret

BattleAnim_Confusion:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_UserObj_2Row
	anim_sound 0, 1, SFX_PSYCHIC
	anim_bgeffect BATTLE_BG_EFFECT_NIGHT_SHADE, $0, BG_EFFECT_TARGET, $8
	anim_wait 128
	anim_incbgeffect BATTLE_BG_EFFECT_NIGHT_SHADE
	anim_call BattleAnim_ShowMon_1
	anim_ret

BattleAnim_Constrict:
	anim_1gfx BATTLE_ANIM_GFX_ROPE
	anim_sound 0, 1, SFX_BIND
	anim_obj BATTLE_ANIM_OBJ_BIND2, 132, 64, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_BIND1, 132, 48, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_BIND2, 132, 40, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_BIND1, 132, 56, $0
	anim_wait 64
	anim_ret

BattleAnim_Earthquake:
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $60, $4, $10
.loop
	anim_sound 0, 1, SFX_EMBER
	anim_wait 24
	anim_loop 4, .loop
	anim_ret

BattleAnim_Fissure:
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $40
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $60, $4, $0
.loop
	anim_sound 0, 1, SFX_EMBER
	anim_wait 24
	anim_loop 4, .loop
	anim_ret

BattleAnim_Growl:
	anim_1gfx BATTLE_ANIM_GFX_NOISE
	anim_battlergfx_2row
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_cry $0
.loop
	anim_call BattleAnimSub_Sound
	anim_wait 16
	anim_loop 3, .loop
	anim_wait 9
	anim_bgeffect BATTLE_BG_EFFECT_BATTLEROBJ_1ROW, $0, BG_EFFECT_USER, $0
	anim_wait 8
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK_REPEATING, $0, BG_EFFECT_TARGET, $40
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK_REPEATING
	anim_wait 1
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 5
	anim_incobj 10
	anim_wait 8
	anim_ret

BattleAnim_Roar:
	anim_1gfx BATTLE_ANIM_GFX_NOISE
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_cry $1
.loop
	anim_call BattleAnimSub_Sound
	anim_wait 16
	anim_loop 3, .loop
	anim_wait 16
	anim_if_param_equal $0, .done
	anim_bgeffect BATTLE_BG_EFFECT_REMOVE_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 64
.done
	anim_ret

BattleAnim_Supersonic:
	anim_1gfx BATTLE_ANIM_GFX_PSYCHIC
.loop
	anim_sound 6, 2, SFX_SUPERSONIC
	anim_obj BATTLE_ANIM_OBJ_WAVE, 64, 88, $2
	anim_wait 4
	anim_loop 10, .loop
	anim_wait 64
	anim_ret

BattleAnim_Screech:
	anim_1gfx BATTLE_ANIM_GFX_PSYCHIC
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $8, $1, $20
	anim_sound 6, 2, SFX_SCREECH
.loop
	anim_obj BATTLE_ANIM_OBJ_WAVE, 64, 88, $2
	anim_wait 2
	anim_loop 2, .loop
	anim_wait 64
	anim_ret

BattleAnim_ConfuseRay:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_BGPALS_INVERTED, $0, $4, $0
	anim_objparams BATTLE_ANIM_OBJ_CONFUSE_RAY, 64, 88, 9, $0, $80, $88, $90, $98, $a0, $a8, $b0, $b8
.loop
	anim_sound 6, 2, SFX_WHIRLWIND
	anim_wait 16
	anim_loop 8, .loop
	anim_wait 32
	anim_ret

BattleAnim_Leer:
	anim_1gfx BATTLE_ANIM_GFX_BEAM
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_call BattleAnimSub_EyeBeams
	anim_wait 16
	anim_ret

BattleAnim_Reflect:
	anim_1gfx BATTLE_ANIM_GFX_REFLECT
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SCREEN, 72, 80, $0
	anim_wait 24
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SCREEN, 72, 80, $0
	anim_wait 64
	anim_ret

BattleAnim_LightScreen:
	anim_2gfx BATTLE_ANIM_GFX_SPEED, BATTLE_ANIM_GFX_REFLECT
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_sound 0, 0, SFX_FLASH
	anim_obj BATTLE_ANIM_OBJ_SCREEN, 72, 80, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SHINY, 72, 80, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SHINY, 72, 80, $8
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SHINY, 72, 80, $10
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SHINY, 72, 80, $18
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SCREEN, 72, 80, $0
	anim_obj BATTLE_ANIM_OBJ_SHINY, 72, 80, $20
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SHINY, 72, 80, $28
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SHINY, 72, 80, $30
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SHINY, 72, 80, $38
	anim_wait 64
	anim_ret

BattleAnim_Amnesia:
	anim_1gfx BATTLE_ANIM_GFX_STATUS
	anim_sound 0, 0, SFX_LICK
	anim_obj BATTLE_ANIM_OBJ_AMNESIA, 64, 80, $2
	anim_wait 16
	anim_obj BATTLE_ANIM_OBJ_AMNESIA, 68, 80, $1
	anim_wait 16
	anim_obj BATTLE_ANIM_OBJ_AMNESIA, 72, 80, $0
	anim_wait 64
	anim_ret

BattleAnim_DizzyPunch:
	anim_2gfx BATTLE_ANIM_GFX_STATUS, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 40, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 136, 64, $0
	anim_wait 16
	anim_sound 0, 1, SFX_KINESIS
	anim_objparams BATTLE_ANIM_OBJ_CHICK, 136, 24, 3, $15, $aa, $bf
	anim_wait 96
	anim_ret

BattleAnim_Rest:
	anim_call BattleAnim_Slp
	anim_ret

BattleAnim_AcidArmor:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_ACID_ARMOR, $0, BG_EFFECT_USER, $8
	anim_sound 0, 0, SFX_MEGA_PUNCH
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_ACID_ARMOR
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Splash:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_VICEGRIP
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_BOUNCE_DOWN, $0, BG_EFFECT_USER, $0
	anim_wait 96
	anim_incbgeffect BATTLE_BG_EFFECT_BOUNCE_DOWN
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Dig:
	anim_2gfx BATTLE_ANIM_GFX_SAND, BATTLE_ANIM_GFX_HIT
	anim_if_param_equal $0, .hit
	anim_if_param_equal $2, .fail
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_DIG, $0, BG_EFFECT_USER, $1
	anim_obj BATTLE_ANIM_OBJ_DIG_PILE, 72, 104, $0
.loop
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_DIG_SAND, 56, 104, $0
	anim_wait 16
	anim_loop 6, .loop
	anim_wait 32
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_DIG
	anim_call BattleAnim_ShowMon_0
	anim_ret

.hit
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 32
.fail
	anim_bgeffect BATTLE_BG_EFFECT_ENTER_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_ret

BattleAnim_SandAttack:
	anim_1gfx BATTLE_ANIM_GFX_SAND
	anim_call BattleAnimSub_SandOrMud
	anim_ret

BattleAnim_StringShot:
	anim_1gfx BATTLE_ANIM_GFX_WEB
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_sound 6, 2, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 64, 80, $0
	anim_wait 4
	anim_sound 0, 1, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 132, 48, $1
	anim_wait 4
	anim_sound 6, 2, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 64, 88, $0
	anim_wait 4
	anim_sound 0, 1, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 132, 64, $1
	anim_wait 4
	anim_sound 6, 2, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 64, 84, $0
	anim_wait 4
	anim_sound 0, 1, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 132, 56, $2
	anim_wait 64
	anim_ret

BattleAnim_Headbutt:
 	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $14, $2, $0
	anim_wait 32
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_HEADBUTT
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 8
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Tackle:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 48, $0
	anim_wait 8
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_BodySlam:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_BOUNCE_DOWN, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_incbgeffect BATTLE_BG_EFFECT_BOUNCE_DOWN
	anim_wait 4
	anim_bgeffect BATTLE_BG_EFFECT_BODY_SLAM, $0, BG_EFFECT_USER, $0
	anim_wait 3
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_wait 6
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_wait 3
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_TakeDown:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 3
	anim_sound 0, 1, SFX_TACKLE
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 56, $0
	anim_wait 6
	anim_sound 0, 1, SFX_TACKLE
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_wait 3
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_DoubleEdge:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $10
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 3
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 128, 48, $0
	anim_wait 6
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 144, 48, $0
	anim_wait 3
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Submission:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_UserObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_WOBBLE_MON, $0, BG_EFFECT_TARGET, $0
	anim_sound 0, 1, SFX_SUBMISSION
	anim_wait 32
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 48, $0
	anim_wait 32
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 152, 56, $0
	anim_wait 32
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 52, $0
	anim_wait 32
	anim_incbgeffect BATTLE_BG_EFFECT_WOBBLE_MON
	anim_call BattleAnim_ShowMon_1
	anim_ret

BattleAnim_Whirlwind:
	anim_1gfx BATTLE_ANIM_GFX_WIND
.loop
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_GUST, 64, 112, $0
	anim_wait 6
	anim_loop 9, .loop
	anim_incobjrange 1, 9
	anim_sound 16, 2, SFX_WHIRLWIND
	anim_wait 128
	anim_if_param_equal $0, .done
	anim_bgeffect BATTLE_BG_EFFECT_REMOVE_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 64
.done
	anim_ret

BattleAnim_Hypnosis:
	anim_1gfx BATTLE_ANIM_GFX_PSYCHIC
.loop
	anim_sound 6, 2, SFX_SUPERSONIC
	anim_obj BATTLE_ANIM_OBJ_WAVE, 64, 88, $2
	anim_obj BATTLE_ANIM_OBJ_WAVE, 56, 80, $2
	anim_wait 8
	anim_loop 3, .loop
	anim_wait 56
	anim_ret

BattleAnim_Haze:
	anim_1gfx BATTLE_ANIM_GFX_HAZE
	anim_sound 0, 1, SFX_SURF
.loop
	anim_obj BATTLE_ANIM_OBJ_HAZE, 48, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HAZE, 132, 16, $0
	anim_wait 12
	anim_loop 5, .loop
	anim_wait 96
	anim_ret

BattleAnim_Mist:
	anim_obp0 $54
	anim_1gfx BATTLE_ANIM_GFX_HAZE
	anim_sound 0, 0, SFX_SURF
.loop
	anim_obj BATTLE_ANIM_OBJ_MIST, 48, 56, $0
	anim_wait 8
	anim_loop 10, .loop
	anim_wait 96
	anim_ret

BattleAnim_Smog:
	anim_1gfx BATTLE_ANIM_GFX_HAZE
	anim_sound 0, 1, SFX_BUBBLEBEAM
.loop
	anim_obj BATTLE_ANIM_OBJ_SMOG, 132, 16, $0
	anim_wait 8
	anim_loop 10, .loop
	anim_wait 96
	anim_ret

BattleAnim_PoisonGas:
	anim_1gfx BATTLE_ANIM_GFX_HAZE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_sound 16, 2, SFX_BUBBLEBEAM
.loop
	anim_obj BATTLE_ANIM_OBJ_POISON_GAS, 44, 80, $2
	anim_wait 8
	anim_loop 10, .loop
	anim_wait 196
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_call BattleAnim_Psn_Target
	anim_wait 8
	anim_ret

BattleAnim_HornAttack:
	anim_2gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_HIT
	anim_obj BATTLE_ANIM_OBJ_HORN, 72, 80, $1
	anim_wait 16
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_FuryAttack:
	anim_2gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_HIT
	anim_obj BATTLE_ANIM_OBJ_HORN, 72, 72, $2
	anim_wait 8
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT, 128, 40, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HORN, 80, 88, $2
	anim_wait 8
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT, 136, 56, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HORN, 76, 80, $2
	anim_wait 8
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT, 132, 48, $0
	anim_wait 8
	anim_ret

BattleAnim_HornDrill:
	anim_2gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $40
	anim_obj BATTLE_ANIM_OBJ_HORN, 72, 80, $3
	anim_wait 8
.loop
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 132, 40, $0
	anim_wait 8
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 140, 48, $0
	anim_wait 8
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 132, 56, $0
	anim_wait 8
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 124, 48, $0
	anim_wait 8
	anim_loop 3, .loop
	anim_ret

BattleAnim_PoisonSting:
	anim_3gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 64, 92, $14
	anim_wait 16
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 136, 56, $0
	anim_wait 16
	anim_call BattleAnimSub_PoisonBubblesEffect
	anim_wait 24
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_Twineedle:
	anim_2gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 64, 92, $14
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 56, 84, $14
	anim_wait 16
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 136, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 128, 48, $0
	anim_wait 16
	anim_ret

BattleAnim_PinMissile:
	anim_2gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_HIT
.loop
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 64, 92, $28
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 56, 84, $28
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 136, 56, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 52, 88, $28
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 128, 48, $0
	anim_wait 8
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 132, 52, $0
	anim_loop 3, .loop
	anim_wait 16
	anim_ret

BattleAnim_SpikeCannon:
	anim_2gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_HIT
.loop
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 64, 92, $18
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 56, 84, $18
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 136, 56, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_NEEDLE, 52, 88, $18
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 128, 48, $0
	anim_wait 8
	anim_sound 0, 1, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL, 132, 52, $0
	anim_loop 3, .loop
	anim_wait 16
	anim_ret

BattleAnim_Transform:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_2Row
	anim_transform
	anim_sound 0, 0, SFX_PSYBEAM
	anim_bgeffect BATTLE_BG_EFFECT_WAVE_DEFORM_MON, $0, BG_EFFECT_USER, $0
	anim_wait 48
	anim_updateactorpic
	anim_incbgeffect BATTLE_BG_EFFECT_WAVE_DEFORM_MON
	anim_wait 48
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_PetalDance:
	anim_sound 0, 0, SFX_MENU
	anim_2gfx BATTLE_ANIM_GFX_FLOWER, BATTLE_ANIM_GFX_HIT
.loop
	anim_obj BATTLE_ANIM_OBJ_PETAL_DANCE, 48, 56, $0
	anim_wait 11
	anim_loop 8, .loop
	anim_wait 192
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_Barrage:
	anim_2gfx BATTLE_ANIM_GFX_EGG, BATTLE_ANIM_GFX_EXPLOSION
	anim_sound 6, 2, SFX_THROW_BALL
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB, 64, 92, $10
	anim_wait 36
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION2, 136, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_PayDay:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_STATUS
	anim_sound 0, 1, SFX_POUND
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 56, $0
	anim_wait 16
	anim_sound 0, 1, SFX_PAY_DAY
	anim_obj BATTLE_ANIM_OBJ_PAY_DAY, 120, 76, $1
	anim_wait 64
	anim_ret

BattleAnim_Mimic:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_obp0 $fc
	anim_sound 63, 3, SFX_LICK
	anim_objparams BATTLE_ANIM_OBJ_MIMIC, 132, 44, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 176
	anim_ret

BattleAnim_LovelyKiss:
	anim_2gfx BATTLE_ANIM_GFX_OBJECTS, BATTLE_ANIM_GFX_ANGELS
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_obj BATTLE_ANIM_OBJ_LOVELY_KISS, 152, 40, $0
	anim_wait 32
	anim_sound 0, 1, SFX_LICK
	anim_obj BATTLE_ANIM_OBJ_HEART, 128, 40, $0
	anim_wait 40
	anim_ret

BattleAnim_Bonemerang:
	anim_2gfx BATTLE_ANIM_GFX_MISC, BATTLE_ANIM_GFX_HIT
	anim_sound 6, 2, SFX_HYDRO_PUMP
	anim_obj BATTLE_ANIM_OBJ_BONEMERANG, 88, 56, $1c
	anim_wait 24
	anim_sound 0, 1, SFX_MOVE_PUZZLE_PIECE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 24
	anim_ret

BattleAnim_Swift:
	anim_1gfx BATTLE_ANIM_GFX_OBJECTS
	anim_sound 6, 2, SFX_METRONOME
	anim_obj BATTLE_ANIM_OBJ_SWIFT, 64, 88, $4
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SWIFT, 64, 72, $4
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SWIFT, 64, 76, $4
	anim_wait 64
	anim_ret

BattleAnim_Crabhammer:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $2, $0
	anim_wait 48
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $3
.loop
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 12
	anim_loop 3, .loop
	anim_ret

BattleAnim_SkullBash:
	anim_if_param_equal $1, BattleAnim_FocusEnergy
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $14, $2, $0
	anim_wait 32
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $3
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
.loop
	anim_sound 0, 1, SFX_HEADBUTT
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 8
	anim_loop 3, .loop
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Kinesis:
	anim_2gfx BATTLE_ANIM_GFX_MISC, BATTLE_ANIM_GFX_NOISE
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_obj BATTLE_ANIM_OBJ_KINESIS, 80, 76, $0
	anim_wait 32
.loop
	anim_sound 0, 0, SFX_KINESIS
	anim_obj BATTLE_ANIM_OBJ_SOUND, 64, 88, $0
	anim_wait 32
	anim_loop 3, .loop
	anim_wait 32
	anim_sound 0, 0, SFX_KINESIS_2
	anim_wait 32
	anim_ret

BattleAnim_Peck:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_PECK
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 128, 48, $0
	anim_wait 8
	anim_sound 0, 1, SFX_PECK
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 136, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_DrillPeck:
	anim_1gfx BATTLE_ANIM_GFX_HIT
.loop
	anim_sound 0, 1, SFX_PECK
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 124, 56, $0
	anim_wait 4
	anim_sound 0, 1, SFX_PECK
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 132, 48, $0
	anim_wait 4
	anim_sound 0, 1, SFX_PECK
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 140, 56, $0
	anim_wait 4
	anim_sound 0, 1, SFX_PECK
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 132, 64, $0
	anim_wait 4
	anim_loop 5, .loop
	anim_wait 16
	anim_ret

BattleAnim_Guillotine:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $10
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $2, $0
	anim_sound 0, 1, SFX_VICEGRIP
	anim_objlist BATTLE_ANIM_OBJ_CUT_DOWN_LEFT, 3, 156, 44, $0, 152, 40, $0, 148, 36, $0
	anim_objlist BATTLE_ANIM_OBJ_CUT_UP_RIGHT, 4, 124, 76, $0, 120, 72, $0, 116, 68, $0, 120, 72, $0
	anim_wait 32
	anim_ret

BattleAnim_Flash:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_sound 0, 1, SFX_FLASH
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $6, $20
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_FLASH, 136, 56, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_FLASH, 136, 56, $8
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_FLASH, 136, 56, $10
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_FLASH, 136, 56, $18
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_FLASH, 136, 56, $20
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_FLASH, 136, 56, $28
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_FLASH, 136, 56, $30
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_FLASH, 136, 56, $38
	anim_wait 32
	anim_ret

BattleAnim_Substitute:
	anim_sound 0, 0, SFX_SURF
	anim_if_param_equal $3, .dropsub2
	anim_if_param_equal $2, .raisesub
	anim_if_param_equal $1, .dropsub
	anim_1gfx BATTLE_ANIM_GFX_SMOKE
	anim_bgeffect BATTLE_BG_EFFECT_REMOVE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 48
	anim_raisesub
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 48, 96, $0
	anim_bgeffect BATTLE_BG_EFFECT_ENTER_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_ret

.dropsub:
	anim_bgeffect BATTLE_BG_EFFECT_REMOVE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 48
	anim_dropsub
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_ret

.raisesub:
	anim_bgeffect BATTLE_BG_EFFECT_REMOVE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 48
	anim_raisesub
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_ret

.dropsub2:
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 48
	anim_dropsub
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_ret

BattleAnim_Minimize:
	anim_sound 0, 0, SFX_SURF
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_2Row
	anim_minimize
	anim_bgeffect BATTLE_BG_EFFECT_WAVE_DEFORM_MON, $0, BG_EFFECT_USER, $0
	anim_wait 48
	anim_updateactorpic
	anim_incbgeffect BATTLE_BG_EFFECT_WAVE_DEFORM_MON
	anim_wait 48
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_SkyAttack:
	anim_if_param_equal $1, BattleAnim_FocusEnergy
	anim_1gfx BATTLE_ANIM_GFX_SKY_ATTACK
	anim_bgeffect BATTLE_BG_EFFECT_REMOVE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_sound 0, 0, SFX_HYPER_BEAM
	anim_obj BATTLE_ANIM_OBJ_SKY_ATTACK, 48, 88, $40
	anim_wait 64
	anim_incobj 1
	anim_wait 21
	anim_sound 0, 1, SFX_HYPER_BEAM
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_wait 64
	anim_incobj 1
	anim_wait 32
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 16
	anim_ret

BattleAnim_NightShade:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgp $1b
	anim_obp1 $1b
	anim_wait 32
	anim_call BattleAnim_UserObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_NIGHT_SHADE, $0, BG_EFFECT_TARGET, $8
	anim_sound 0, 1, SFX_PSYCHIC
	anim_wait 96
	anim_incbgeffect BATTLE_BG_EFFECT_NIGHT_SHADE
	anim_call BattleAnim_ShowMon_1
	anim_ret

BattleAnim_Lick:
	anim_1gfx BATTLE_ANIM_GFX_WATER
	anim_sound 0, 1, SFX_LICK
	anim_obj BATTLE_ANIM_OBJ_LICK, 136, 56, $0
	anim_wait 64
	anim_ret

BattleAnim_TriAttack:
	anim_3gfx BATTLE_ANIM_GFX_EMBER, BATTLE_ANIM_GFX_ICE, BATTLE_ANIM_GFX_THUNDER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
	anim_call BattleAnimSub_Fire
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_wait 16
	anim_call BattleAnimSub_Ice
	anim_wait 20
	anim_thunderpal BATTLE_ANIM_THUNDER_PAL_LOAD
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $4
	anim_sound 0, 1, SFX_THUNDER
	anim_obj BATTLE_ANIM_OBJ_THUNDER_STRIKE_CONTROLLER, 136, 0, $0
	anim_wait 67
	anim_thunderpal BATTLE_ANIM_THUNDER_PAL_RESTORE
	anim_ret

BattleAnim_Withdraw:
	anim_1gfx BATTLE_ANIM_GFX_REFLECT
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_WITHDRAW, $0, BG_EFFECT_USER, $50
	anim_wait 48
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_WITHDRAW, 48, 88, $0
	anim_wait 64
	anim_incobj 2
	anim_wait 1
	anim_incbgeffect BATTLE_BG_EFFECT_WITHDRAW
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Psybeam:
	anim_1gfx BATTLE_ANIM_GFX_PSYCHIC
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_BGPALS_INVERTED, $0, $4, $0
.loop
	anim_sound 6, 2, SFX_PSYBEAM
	anim_obj BATTLE_ANIM_OBJ_WAVE, 64, 88, $4
	anim_wait 4
	anim_loop 10, .loop
	anim_wait 48
	anim_ret

BattleAnim_DreamEater:
	anim_1gfx BATTLE_ANIM_GFX_BUBBLE
	anim_bgp $1b
	anim_obp0 $27
	anim_sound 6, 3, SFX_WATER_GUN
	anim_call BattleAnimSub_Drain
	anim_wait 176
	anim_ret

BattleAnim_LeechLife:
	anim_1gfx BATTLE_ANIM_GFX_BUBBLE
	anim_sound 6, 3, SFX_WATER_GUN
	anim_call BattleAnimSub_Drain
	anim_wait 176
	anim_ret

BattleAnim_Harden:
	anim_1gfx BATTLE_ANIM_GFX_REFLECT
	anim_obp0 $0
	anim_call BattleAnim_TargetObj_1Row
	anim_call BattleAnimSub_Metallic
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Psywave:
	anim_1gfx BATTLE_ANIM_GFX_PSYCHIC
	anim_bgeffect BATTLE_BG_EFFECT_PSYCHIC, $0, $0, $0
.loop
	anim_sound 6, 2, SFX_PSYCHIC
	anim_obj BATTLE_ANIM_OBJ_WAVE, 64, 80, $2
	anim_wait 8
	anim_sound 6, 2, SFX_PSYCHIC
	anim_obj BATTLE_ANIM_OBJ_WAVE, 64, 88, $3
	anim_wait 8
	anim_sound 6, 2, SFX_PSYCHIC
	anim_obj BATTLE_ANIM_OBJ_WAVE, 64, 96, $4
	anim_wait 8
	anim_loop 3, .loop
	anim_wait 32
	anim_incbgeffect BATTLE_BG_EFFECT_PSYCHIC
	anim_wait 4
	anim_ret

BattleAnim_Glare:
	anim_1gfx BATTLE_ANIM_GFX_BEAM
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $20
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_call BattleAnimSub_EyeBeams
	anim_wait 16
	anim_ret

BattleAnim_Thrash:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_POUND
	anim_obj BATTLE_ANIM_OBJ_PALM, 120, 72, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 120, 72, $0
	anim_wait 6
	anim_sound 0, 1, SFX_MOVE_PUZZLE_PIECE
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 6
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 152, 40, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 152, 40, $0
	anim_wait 16
	anim_ret

BattleAnim_Growth:
	anim_bgeffect BATTLE_BG_EFFECT_WHITE_HUES, $0, $8, $0
	anim_1gfx BATTLE_ANIM_GFX_CHARGE
	anim_sound 0, 0, SFX_SWORDS_DANCE
	anim_objparams BATTLE_ANIM_OBJ_GROWTH, 48, 108, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 64
	anim_ret

BattleAnim_Conversion2:
	anim_1gfx BATTLE_ANIM_GFX_EXPLOSION
	anim_sound 63, 3, SFX_SHARPEN
	anim_objparams BATTLE_ANIM_OBJ_CONVERSION2, 132, 44, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 176
	anim_ret

BattleAnim_Smokescreen:
	anim_3gfx BATTLE_ANIM_GFX_HAZE, BATTLE_ANIM_GFX_EGG, BATTLE_ANIM_GFX_SMOKE
	anim_sound 6, 2, SFX_THROW_BALL
	anim_obj BATTLE_ANIM_OBJ_SMOKESCREEN, 64, 92, $6c
	anim_wait 24
	anim_incobj 1
	anim_sound 0, 1, SFX_BALL_POOF
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 108, 70, $10
	anim_wait 8
.loop
	anim_sound 0, 1, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_SMOKE, 132, 60, $20
	anim_wait 8
	anim_loop 5, .loop
	anim_wait 128
	anim_ret

BattleAnim_Strength:
	anim_2gfx BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_Y, $10, $1, $20
	anim_sound 0, 0, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_STRENGTH, 64, 104, $1
	anim_wait 128
	anim_incobj 1
	anim_wait 20
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 132, 40, $0
	anim_wait 16
	anim_ret

BattleAnim_SwordsDance:
	anim_1gfx BATTLE_ANIM_GFX_WHIP
	anim_sound 0, 0, SFX_SWORDS_DANCE
	anim_objparams BATTLE_ANIM_OBJ_SWORDS_DANCE, 48, 108, 5, $0, $d, $1a, $27, $34
	anim_wait 56
	anim_ret

BattleAnim_QuickAttack:
	anim_2gfx BATTLE_ANIM_GFX_SPEED, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_MENU
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_call BattleAnimSub_SpeedLineBurst
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 8
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 16
	anim_ret

BattleAnim_Meditate:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_sound 0, 0, SFX_PSYBEAM
	anim_bgeffect BATTLE_BG_EFFECT_WAVE_DEFORM_MON, $0, BG_EFFECT_USER, $0
	anim_wait 48
	anim_incbgeffect BATTLE_BG_EFFECT_WAVE_DEFORM_MON
	anim_wait 48
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Sharpen:
	anim_1gfx BATTLE_ANIM_GFX_SHAPES
	anim_obp0 $e4
	anim_call BattleAnim_TargetObj_1Row
	anim_sound 0, 0, SFX_SHARPEN
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING, $0, BG_EFFECT_USER, $40
	anim_obj BATTLE_ANIM_OBJ_SHARPEN, 48, 88, $0
	anim_wait 96
	anim_incobj 2
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_DefenseCurl:
	anim_1gfx BATTLE_ANIM_GFX_SHAPES
	anim_obp0 $e4
	anim_call BattleAnim_TargetObj_1Row
	anim_sound 0, 0, SFX_SHARPEN
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING, $0, BG_EFFECT_USER, $40
	anim_obj BATTLE_ANIM_OBJ_DEFENSE_CURL, 48, 88, $0
	anim_wait 96
	anim_incobj 2
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_SeismicToss:
;	This is the old Seismic Toss animation, which I'm keeping for future reference.
;	anim_2gfx BATTLE_ANIM_GFX_GLOBE, BATTLE_ANIM_GFX_HIT
;	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_Y, $10, $1, $20
;	anim_sound 0, 0, SFX_STRENGTH
;	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS, 64, 104, $1
;	anim_wait 128
;	anim_incobj 1
;	anim_wait 20
;	anim_sound 0, 1, SFX_MEGA_PUNCH
;	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 132, 40, $0
;	anim_wait 16
	anim_3gfx BATTLE_ANIM_GFX_SPEED, BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_Y, $10, $1, $20
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 12, 224, $7
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 28, 184, $6
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 20, 160, $5
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 28, 152, $4
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 20, 160, $3
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 28, 180, $2
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 12, 212, $1
	anim_wait 24
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 12, 0, $81
	anim_wait 22
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 28, 0, $82
	anim_wait 17
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 20, 0, $83
	anim_wait 15
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 28, 0, $84
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 20, 4, $85
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 12, 8, $86
	anim_wait 12
	anim_sound 0, 1, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 56, $0
	anim_call BattleAnimSub_RockSmashRocks
	anim_wait 32
	anim_ret

BattleAnim_Rage:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING, $0, BG_EFFECT_USER, $20
	anim_sound 0, 0, SFX_RAGE
	anim_wait 72
	anim_incbgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_sound 0, 1, SFX_MOVE_PUZZLE_PIECE
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 120, 72, $0
	anim_wait 6
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 6
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 152, 40, $0
	anim_wait 16
	anim_ret

BattleAnim_Agility:
	anim_1gfx BATTLE_ANIM_GFX_WIND
	anim_obp0 $fc
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING, $0, BG_EFFECT_USER, $40
	anim_call BattleAnimSub_AgilityWindLines
.loop
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_wait 4
	anim_loop 18, .loop
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_BoneClub:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_MISC
	anim_obj BATTLE_ANIM_OBJ_BONE_CLUB, 64, 88, $2
	anim_wait 32
	anim_sound 0, 1, SFX_BONE_CLUB
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_Barrier:
	anim_1gfx BATTLE_ANIM_GFX_REFLECT
	anim_battlergfx_2row
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_wait 8
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SCREEN, 72, 80, $0
	anim_wait 32
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SCREEN, 72, 80, $0
	anim_wait 32
	anim_ret

BattleAnim_Waterfall:
	anim_3gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_WATER, BATTLE_ANIM_GFX_SMALL_BUBBLE
	anim_waterpal BATTLE_ANIM_WATER_PAL_LOAD
	anim_sound 0, 1, SFX_HYDRO_PUMP
	anim_bgeffect BATTLE_BG_EFFECT_WHIRLPOOL, $0, $0, $0
	anim_wait 36
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP, 108, 32, $0
	anim_wait 19
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP, 116, 32, $0
	anim_wait 19
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP, 124, 32, $0
	anim_wait 19
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP, 132, 32, $0
	anim_wait 19
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP, 140, 32, $0
	anim_wait 19
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP, 148, 32, $0
	anim_wait 19
	anim_obj BATTLE_ANIM_OBJ_HYDRO_PUMP, 156, 32, $0
	anim_wait 21
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_HIT_SMALL, 136, 64, $0
	anim_wait 3
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_HIT_SMALL, 136, 56, $0
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 120, 64, $0
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 148, 60, $1
	anim_wait 3
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_HIT_SMALL, 136, 48, $0
	anim_wait 3
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_HIT_SMALL, 136, 40, $0
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 128, 48, $2
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 156, 52, $3
	anim_wait 3
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_HIT_SMALL, 136, 32, $0
	anim_wait 3
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 116, 40, $0
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 144, 36, $1
	anim_wait 29
	anim_incbgeffect BATTLE_BG_EFFECT_WHIRLPOOL
	anim_wait 12
	anim_waterpal BATTLE_ANIM_WATER_PAL_RESTORE
	anim_ret

BattleAnim_PsychicM:
	anim_1gfx BATTLE_ANIM_GFX_PSYCHIC
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_PSYCHIC, $0, $0, $0
.loop
	anim_sound 6, 2, SFX_PSYCHIC
	anim_obj BATTLE_ANIM_OBJ_WAVE, 64, 88, $2
	anim_wait 8
	anim_loop 8, .loop
	anim_wait 96
	anim_incbgeffect BATTLE_BG_EFFECT_PSYCHIC
	anim_wait 4
	anim_ret

BattleAnim_Sludge:
	anim_1gfx BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_sound 6, 2, SFX_SLUDGE_BOMB
	anim_obj BATTLE_ANIM_OBJ_POISON_SLUDGE, 64, 92, $10
	anim_wait 36
	anim_call BattleAnimSub_PoisonBubblesEffect
	anim_wait 24
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_Toxic:
	anim_2gfx BATTLE_ANIM_GFX_TOXIC_BUBBLE, BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_call BattleAnimSub_ToxicBubbles
	anim_call BattleAnimSub_ToxicBubbles
	anim_wait 20
	anim_call BattleAnimSub_PoisonBubblesEffect
	anim_wait 24
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_Metronome:
	anim_2gfx BATTLE_ANIM_GFX_MISC, BATTLE_ANIM_GFX_SPEED
	anim_sound 0, 0, SFX_METRONOME
	anim_obj BATTLE_ANIM_OBJ_METRONOME_HAND, 72, 88, $0
.loop
	anim_obj BATTLE_ANIM_OBJ_METRONOME_SPARKLE, 72, 80, $0
	anim_wait 8
	anim_loop 5, .loop
	anim_wait 48
	anim_ret

BattleAnim_Counter:
	anim_1gfx BATTLE_ANIM_GFX_HIT
.loop
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $6, $2
	anim_sound 0, 1, SFX_POUND
	anim_obj BATTLE_ANIM_OBJ_PALM, 120, 72, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 120, 72, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $6, $2
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 40, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 40, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $6, $2
	anim_sound 0, 1, SFX_MEGA_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 152, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 152, 56, $0
	anim_wait 6
	anim_loop 3, .loop
	anim_wait 16
	anim_ret

BattleAnim_LowKick:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 124, 64, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 124, 64, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 132, 64, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 132, 64, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 140, 64, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 140, 64, $0
	anim_wait 16
	anim_ret

BattleAnim_WingAttack:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnimSub_WingAttackHits
	anim_ret

BattleAnim_Slam:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_WING_ATTACK
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $2
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 124, 40, $0
	anim_wait 16
	anim_ret

BattleAnim_Disable:
	anim_2gfx BATTLE_ANIM_GFX_LIGHTNING, BATTLE_ANIM_GFX_STATUS
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_obj BATTLE_ANIM_OBJ_DISABLE, 132, 56, $0
	anim_wait 16
	anim_sound 0, 1, SFX_BIND
	anim_obj BATTLE_ANIM_OBJ_PARALYZED, 104, 56, $42
	anim_obj BATTLE_ANIM_OBJ_PARALYZED, 160, 56, $c2
	anim_wait 96
	anim_ret

BattleAnim_TailWhip:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_2Row
	anim_sound 0, 0, SFX_TAIL_WHIP
	anim_bgeffect BATTLE_BG_EFFECT_WOBBLE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 32
	anim_incbgeffect BATTLE_BG_EFFECT_WOBBLE_MON
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Struggle:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_POUND
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_Sketch:
	anim_1gfx BATTLE_ANIM_GFX_OBJECTS
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING, $0, BG_EFFECT_USER, $20
	anim_sound 0, 0, SFX_SKETCH
	anim_obj BATTLE_ANIM_OBJ_SKETCH, 72, 80, $0
	anim_wait 80
	anim_incbgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_wait 1
	anim_ret

BattleAnim_TripleKick:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_if_param_equal $1, .alternate1
	anim_if_param_equal $2, .alternate2
	anim_sound 0, 1, SFX_MEGA_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 144, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_wait 8
	anim_ret

.alternate1:
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 120, 64, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 64, $0
	anim_wait 8
	anim_ret

.alternate2:
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 132, 32, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 132, 32, $0
	anim_wait 8
	anim_ret

BattleAnim_Thief:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 16
	anim_sound 0, 1, SFX_THIEF
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 48, $0
	anim_wait 16
	anim_call BattleAnim_ShowMon_0
	anim_wait 1
	anim_1gfx BATTLE_ANIM_GFX_STATUS
	anim_sound 0, 1, SFX_THIEF_2
	anim_obj BATTLE_ANIM_OBJ_THIEF, 120, 76, $1
	anim_wait 64
	anim_ret

BattleAnim_SpiderWeb:
	anim_1gfx BATTLE_ANIM_GFX_WEB
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_obj BATTLE_ANIM_OBJ_SPIDER_WEB, 132, 48, $0
	anim_sound 6, 2, SFX_SPIDER_WEB
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 64, 80, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 64, 88, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_STRING_SHOT, 64, 84, $0
	anim_wait 64
	anim_ret

BattleAnim_MindReader:
	anim_1gfx BATTLE_ANIM_GFX_MISC
	anim_sound 0, 1, SFX_MIND_READER
.loop
	anim_objparams BATTLE_ANIM_OBJ_MIND_READER, 132, 48, 4, $3, $12, $20, $31
	anim_wait 16
	anim_loop 2, .loop
	anim_wait 32
	anim_ret

BattleAnim_Nightmare:
	anim_1gfx BATTLE_ANIM_GFX_ANGELS
	anim_bgp $1b
	anim_obp0 $f
	anim_objparams BATTLE_ANIM_OBJ_NIGHTMARE, 132, 40, 2, $0, $a0
	anim_sound 0, 1, SFX_NIGHTMARE
	anim_wait 96
	anim_ret

BattleAnim_FlameWheel:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
.loop
	anim_sound 0, 0, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FLAME_WHEEL, 48, 96, $0
	anim_wait 6
	anim_loop 8, .loop
	anim_wait 96
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $3
	anim_call BattleAnimSub_Fire
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 4
	anim_incobj 9
	anim_wait 8
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnim_Snore:
	anim_2gfx BATTLE_ANIM_GFX_STATUS, BATTLE_ANIM_GFX_NOISE
	anim_obj BATTLE_ANIM_OBJ_ASLEEP, 64, 80, $0
	anim_wait 32
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $60, $2, $0
	anim_sound 0, 0, SFX_SNORE
.loop
	anim_call BattleAnimSub_Sound
	anim_wait 16
	anim_loop 2, .loop
	anim_wait 8
	anim_ret

BattleAnim_Curse:
	anim_if_param_equal $1, .NotGhost
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_OBJECTS
	anim_obj BATTLE_ANIM_OBJ_CURSE, 68, 72, $0
	anim_sound 0, 0, SFX_CURSE
	anim_wait 32
	anim_incobj 1
	anim_wait 12
	anim_sound 0, 0, SFX_POISON_STING
	anim_obj BATTLE_ANIM_OBJ_HIT, 44, 96, $0
	anim_wait 16
	anim_ret

.NotGhost:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK_REPEATING, $0, BG_EFFECT_USER, $40
	anim_sound 0, 0, SFX_SHARPEN
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK_REPEATING
	anim_wait 1
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT, $0, BG_EFFECT_USER, $40
.loop
	anim_call BattleAnimSub_FocusEnergyBurst
	anim_loop 3, .loop
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Flail:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_sound 0, 0, SFX_SUBMISSION
	anim_bgeffect BATTLE_BG_EFFECT_FLAIL, $0, BG_EFFECT_USER, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 48, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 152, 48, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_FLAIL
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Conversion:
	anim_1gfx BATTLE_ANIM_GFX_EXPLOSION
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_sound 63, 3, SFX_SHARPEN
	anim_objparams BATTLE_ANIM_OBJ_CONVERSION, 48, 88, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 128
	anim_ret

BattleAnim_Aeroblast:
	anim_2gfx BATTLE_ANIM_GFX_BEAM, BATTLE_ANIM_GFX_AEROBLAST
	anim_bgp $1b
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $50, $4, $10
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_sound 0, 0, SFX_AEROBLAST
	anim_obj BATTLE_ANIM_OBJ_AEROBLAST, 72, 88, $0
	anim_wait 32
	anim_sound 0, 0, SFX_HYPER_BEAM
	anim_obj BATTLE_ANIM_OBJ_BEAM, 80, 84, $0
	anim_wait 2
	anim_sound 0, 1, SFX_HYPER_BEAM
	anim_obj BATTLE_ANIM_OBJ_BEAM, 96, 76, $0
	anim_wait 2
	anim_sound 0, 1, SFX_HYPER_BEAM
	anim_obj BATTLE_ANIM_OBJ_BEAM, 112, 68, $0
	anim_obj BATTLE_ANIM_OBJ_BEAM_TIP, 126, 62, $0
	anim_wait 48
	anim_ret

BattleAnim_CottonSpore:
	anim_obp0 $54
	anim_1gfx BATTLE_ANIM_GFX_MISC
	anim_sound 0, 1, SFX_POWDER
.loop
	anim_obj BATTLE_ANIM_OBJ_COTTON_SPORE, 132, 32, $0
	anim_wait 8
	anim_loop 5, .loop
	anim_wait 96
	anim_ret

BattleAnim_Reversal:
	anim_2gfx BATTLE_ANIM_GFX_SHINE, BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT, 112, 64, $0
	anim_wait 2
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_FORESIGHT, 120, 56, $0
	anim_wait 2
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT, 128, 56, $0
	anim_wait 2
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_FORESIGHT, 136, 48, $0
	anim_wait 2
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT, 144, 48, $0
	anim_wait 2
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_FORESIGHT, 152, 40, $0
	anim_wait 24
	anim_ret

BattleAnim_Spite:
	anim_1gfx BATTLE_ANIM_GFX_ANGELS
	anim_obj BATTLE_ANIM_OBJ_SPITE, 132, 16, $0
	anim_sound 0, 1, SFX_SPITE
	anim_wait 96
	anim_ret

BattleAnim_PowderSnow:
	anim_1gfx BATTLE_ANIM_GFX_ICE
.loop
	anim_sound 6, 2, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_POWDER_SNOW, 64, 88, $23
	anim_wait 2
	anim_sound 6, 2, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_POWDER_SNOW, 64, 80, $24
	anim_wait 2
	anim_sound 6, 2, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_POWDER_SNOW, 64, 96, $23
	anim_wait 2
	anim_loop 2, .loop
	anim_bgeffect BATTLE_BG_EFFECT_WHITE_HUES, $0, $8, $0
	anim_wait 40
	anim_call BattleAnimSub_Ice
	anim_wait 32
	anim_ret

BattleAnim_Protect:
	anim_1gfx BATTLE_ANIM_GFX_OBJECTS
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_objparams BATTLE_ANIM_OBJ_PROTECT, 80, 80, 5, $0, $d, $1a, $27, $34
	anim_sound 0, 0, SFX_PROTECT
	anim_wait 96
	anim_ret

BattleAnim_MachPunch:
	anim_2gfx BATTLE_ANIM_GFX_SPEED, BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_sound 0, 0, SFX_MENU
	anim_call BattleAnimSub_SpeedLineBurst
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 56, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 8
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 16
	anim_ret

BattleAnim_ScaryFace:
	anim_1gfx BATTLE_ANIM_GFX_BEAM
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_call BattleAnimSub_EyeBeams
	anim_wait 64
	anim_ret

BattleAnim_FaintAttack:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_CURSE
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_WHITE_WAIT_FADE_BACK, $0, BG_EFFECT_USER, $80
	anim_wait 96
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT, 120, 32, $0
	anim_wait 8
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT, 152, 40, $0
	anim_wait 8
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT, 136, 48, $0
	anim_wait 32
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_WHITE_WAIT_FADE_BACK
	anim_call BattleAnim_ShowMon_0
	anim_wait 4
	anim_ret

BattleAnim_SweetKiss:
	anim_2gfx BATTLE_ANIM_GFX_OBJECTS, BATTLE_ANIM_GFX_ANGELS
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_obj BATTLE_ANIM_OBJ_SWEET_KISS, 96, 40, $0
	anim_sound 0, 1, SFX_SWEET_KISS
	anim_wait 32
	anim_sound 0, 1, SFX_SWEET_KISS_2
	anim_obj BATTLE_ANIM_OBJ_HEART, 120, 40, $0
	anim_wait 40
	anim_ret

BattleAnim_BellyDrum:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_NOISE
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 24
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 24
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 12
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 12
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 24
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 12
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 12
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 12
	anim_sound 0, 0, SFX_BELLY_DRUM
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_HAND, 64, 104, $0
	anim_obj BATTLE_ANIM_OBJ_BELLY_DRUM_NOTE, 64, 92, $f8
	anim_wait 12
	anim_ret

BattleAnim_SludgeBomb:
	anim_2gfx BATTLE_ANIM_GFX_SLUDGE_BOMB, BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_sound 6, 2, SFX_SLUDGE_BOMB
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_PROJECTILE, 64, 92, $18
	anim_wait 38
	anim_call BattleAnimSub_SludgeBombImpact
	anim_wait 28
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnimSub_SludgeBombImpact:
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_SPLATTER, 136, 68, $80
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_BUBBLE, 120, 50, $80
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_SPLATTER, 124, 66, $80
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_SPLATTER, 148, 64, $80
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_BUBBLE, 152, 48, $80
	anim_wait 4
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_SPLATTER, 128, 60, $80
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_BUBBLE, 128, 42, $80
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_SPLATTER, 144, 56, $80
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_BUBBLE, 148, 38, $80
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_SPLATTER, 120, 54, $80
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_SLUDGE_BOMB_TARGET_SPLATTER, 152, 52, $80
	anim_wait 4
	anim_ret

BattleAnimSub_PoisonSludgeArc:
	anim_sound 6, 2, SFX_BUBBLEBEAM
.loop
	anim_obj BATTLE_ANIM_OBJ_POISON_SLUDGE, 64, 92, $10
	anim_wait 5
	anim_loop 8, .loop
	anim_ret

BattleAnimSub_PoisonSplatter:
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_POISON_SPLATTER, 132, 36, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_POISON_SPLATTER, 120, 40, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_POISON_SPLATTER, 144, 44, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_POISON_SPLATTER, 126, 49, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_POISON_SPLATTER, 140, 53, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_POISON_SPLATTER, 118, 57, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TOXIC
	anim_obj BATTLE_ANIM_OBJ_POISON_SPLATTER, 146, 61, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_POISON_SPLATTER, 134, 65, $0
	anim_wait 4
	anim_ret

BattleAnim_MudSlap:
	anim_1gfx BATTLE_ANIM_GFX_SAND
	anim_obp0 $fc
	anim_call BattleAnimSub_SandOrMud
	anim_ret

BattleAnim_Octazooka:
	anim_3gfx BATTLE_ANIM_GFX_HAZE, BATTLE_ANIM_GFX_EGG, BATTLE_ANIM_GFX_SMOKE
	anim_sound 6, 2, SFX_SLUDGE_BOMB
	anim_obj BATTLE_ANIM_OBJ_OCTAZOOKA, 64, 92, $4
	anim_wait 16
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 132, 56, $10
	anim_wait 8
	anim_if_param_equal $0, .done
.loop
	anim_obj BATTLE_ANIM_OBJ_SMOKE, 132, 60, $20
	anim_wait 8
	anim_loop 5, .loop
	anim_wait 128
.done
	anim_ret

BattleAnim_Spikes:
	anim_1gfx BATTLE_ANIM_GFX_MISC
	anim_sound 6, 2, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_SPIKES, 48, 88, $20
	anim_wait 8
	anim_sound 6, 2, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_SPIKES, 48, 88, $30
	anim_wait 8
	anim_sound 6, 2, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_SPIKES, 48, 88, $28
	anim_wait 64
	anim_ret

BattleAnim_ZapCannon:
	anim_2gfx BATTLE_ANIM_GFX_LIGHTNING, BATTLE_ANIM_GFX_EXPLOSION
	anim_bgp $1b
	anim_obp0 $30
	anim_sound 6, 2, SFX_ZAP_CANNON
	anim_obj BATTLE_ANIM_OBJ_ZAP_CANNON, 64, 92, $2
	anim_wait 40
	anim_sound 0, 1, SFX_THUNDERSHOCK
	anim_obj BATTLE_ANIM_OBJ_THUNDERBOLT_BALL, 136, 56, $2
	anim_wait 16
	anim_obj BATTLE_ANIM_OBJ_SPARKS_CIRCLE_BIG, 136, 56, $0
	anim_wait 128
	anim_ret

BattleAnim_Foresight:
	anim_1gfx BATTLE_ANIM_GFX_SHINE
	anim_call BattleAnim_UserObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
	anim_sound 0, 1, SFX_FORESIGHT
	anim_obj BATTLE_ANIM_OBJ_FORESIGHT, 132, 40, $0
	anim_wait 24
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK_REPEATING, $0, BG_EFFECT_TARGET, $40
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK_REPEATING
	anim_call BattleAnim_ShowMon_1
	anim_wait 8
	anim_ret

BattleAnim_DestinyBond:
	anim_1gfx BATTLE_ANIM_GFX_ANGELS
	anim_bgp $1b
	anim_obp0 $0
	anim_if_param_equal $1, .fainted
	anim_sound 6, 2, SFX_WHIRLWIND
	anim_obj BATTLE_ANIM_OBJ_DESTINY_BOND, 44, 120, $2
	anim_wait 128
	anim_ret

.fainted:
	anim_obj BATTLE_ANIM_OBJ_DESTINY_BOND, 132, 76, $0
	anim_sound 0, 1, SFX_KINESIS
	anim_bgeffect BATTLE_BG_EFFECT_RETURN_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 32
	anim_ret

BattleAnim_PerishSong:
	anim_1gfx BATTLE_ANIM_GFX_NOISE
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_sound 0, 2, SFX_PERISH_SONG
	anim_objparams BATTLE_ANIM_OBJ_PERISH_SONG, 88, 0, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 112
	anim_ret

BattleAnim_IcyWind:
	anim_1gfx BATTLE_ANIM_GFX_ICE
.loop
	anim_call BattleAnimSub_BlizzardSweep
	anim_loop 2, .loop
	anim_wait 2
	anim_bgeffect BATTLE_BG_EFFECT_WHITE_HUES, $0, $8, $0
	anim_wait 40
	anim_call BattleAnimSub_Ice
	anim_wait 32
	anim_ret

BattleAnim_Detect:
	anim_1gfx BATTLE_ANIM_GFX_SHINE
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
	anim_sound 0, 0, SFX_FORESIGHT
	anim_obj BATTLE_ANIM_OBJ_FORESIGHT, 64, 88, $0
	anim_wait 24
	anim_ret

BattleAnim_BoneRush:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_MISC
	anim_sound 0, 1, SFX_BONE_CLUB
	anim_obj BATTLE_ANIM_OBJ_BONE_RUSH, 132, 56, $2
	anim_wait 16
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 48, $0
	anim_wait 16
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 64, $0
	anim_wait 16
	anim_ret

BattleAnim_LockOn:
	anim_1gfx BATTLE_ANIM_GFX_MISC
	anim_sound 0, 1, SFX_MIND_READER
.loop
	anim_objparams BATTLE_ANIM_OBJ_LOCK_ON, 132, 48, 4, $3, $12, $20, $31
	anim_wait 16
	anim_loop 2, .loop
	anim_wait 32
	anim_ret

BattleAnim_Outrage:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_LOAD
.loop
	anim_sound 0, 0, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_SACRED_FIRE, 48, 104, $0
	anim_wait 8
	anim_loop 8, .loop
	anim_wait 60
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $60, $2, $10
	anim_sound 0, 1, SFX_EMBER
.burst_loop
	anim_call BattleAnimSub_OutrageFlameBurstA
	anim_wait 16
	anim_call BattleAnimSub_OutrageFlameBurstB
	anim_wait 16
	anim_loop 2, .burst_loop
	anim_call BattleAnimSub_OutrageFlameBurstA
	anim_wait 52
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_RESTORE
	anim_ret

BattleAnimSub_OutrageFlameBurstA:
	anim_objparams BATTLE_ANIM_OBJ_OUTRAGE_FLAME, 48, 96, 4, $0, $3, $5, $2
	anim_ret

BattleAnimSub_OutrageFlameBurstB:
	anim_objparams BATTLE_ANIM_OBJ_OUTRAGE_FLAME, 48, 96, 4, $1, $4, $7, $6
	anim_ret

BattleAnim_Sandstorm:
	anim_1gfx BATTLE_ANIM_GFX_POWDER
	anim_call BattleAnimSub_SandstormStart
.loop
	anim_sound 0, 1, SFX_MENU
	anim_wait 8
	anim_loop 16, .loop
	anim_wait 8
	anim_ret

BattleAnim_FakeOut:
	anim_2gfx BATTLE_ANIM_GFX_OBJECTS, BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_UserObj_1Row
	anim_extobj BATTLE_ANIM_EXT_OBJ_FAKE_OUT_HAND, 104, 48, $0
	anim_extobj BATTLE_ANIM_EXT_OBJ_FAKE_OUT_HAND, 168, 48, $1
	anim_wait 8
	anim_sound 0, 1, SFX_DOUBLESLAP
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_bgeffect BATTLE_BG_EFFECT_VIBRATE_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 34
	anim_call BattleAnim_ShowMon_1
	anim_ret

BattleAnim_HeatWave:
	anim_bgeffect BATTLE_BG_EFFECT_FIRE_BGPALS, $0, $0, $82
	anim_bgeffect BATTLE_BG_EFFECT_WHIRLPOOL, $0, $0, $0
	anim_sound 6, 2, SFX_EMBER
	anim_wait 128
	anim_incbgeffect BATTLE_BG_EFFECT_WHIRLPOOL
	anim_wait 8
	anim_ret

BattleAnim_Hail:
	anim_call BattleAnimSub_HailWeather
.loop
	anim_sound 0, 1, SFX_SHINE
	anim_wait 8
	anim_loop 16, .loop
	anim_wait 8
	anim_ret

BattleAnim_WillOWisp:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
.loop1
	anim_bgp $1b
	anim_call BattleAnimSub_FireSpinOpener
	anim_loop 2, .loop1
	anim_wait 120
.loop2
	anim_sound 0, 0, SFX_BURN
	anim_objparams BATTLE_ANIM_OBJ_BURNED, 136, 56, 2, $10, $90
	anim_wait 4
	anim_loop 3, .loop2
	anim_wait 16
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnim_FocusPunch:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_battlergfx_2row
	anim_bgeffect BATTLE_BG_EFFECT_BATTLEROBJ_1ROW, $0, BG_EFFECT_TARGET, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT, $0, BG_EFFECT_USER, $40
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
.loop
	anim_call BattleAnimSub_FocusEnergyBurst
	anim_loop 3, .loop
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT
	anim_wait 1
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 5
	anim_incobj 1
	anim_wait 1
	anim_2gfx BATTLE_ANIM_GFX_FOCUS_PUNCH, BATTLE_ANIM_GFX_HIT
	anim_extobj BATTLE_ANIM_EXT_OBJ_FOCUS_PUNCH_FIST, 136, 52, $43
	anim_wait 4
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $60, $4, $0
	anim_wait 6
	anim_call BattleAnimSub_FocusPunchHits
	anim_wait 8
	anim_ret

BattleAnim_Taunt:
	anim_4gfx BATTLE_ANIM_GFX_THOUGHT_BUBBLE_4, BATTLE_ANIM_GFX_THOUGHT_BUBBLE_1, BATTLE_ANIM_GFX_THOUGHT_BUBBLE_2, BATTLE_ANIM_GFX_THOUGHT_BUBBLE_3
	anim_sound 0, 0, SFX_METRONOME
	anim_extobj BATTLE_ANIM_EXT_OBJ_TAUNT_THOUGHT_1, 0, 0, $00
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_TAUNT_THOUGHT_2, 0, 0, $00
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_TAUNT_THOUGHT_3, 0, 0, $00
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_TAUNT_THOUGHT_4, 0, 0, $00
	anim_wait 6
	anim_2gfx BATTLE_ANIM_GFX_THOUGHT_BUBBLE_4, BATTLE_ANIM_GFX_TAUNT_FINGER
	anim_extobj BATTLE_ANIM_EXT_OBJ_TAUNT_FINGER, 0, 0, $03
	anim_wait 4
	anim_sound 0, 0, SFX_TAIL_WHIP
	anim_wait 40
	anim_clearobjs
	anim_1gfx BATTLE_ANIM_GFX_TAUNT_ANGER
	anim_sound 0, 1, SFX_KINESIS_2
	anim_extobj BATTLE_ANIM_EXT_OBJ_TAUNT_ANGER, 0, 0, $01
	anim_wait 20
	anim_sound 0, 1, SFX_KINESIS_2
	anim_extobj BATTLE_ANIM_EXT_OBJ_TAUNT_ANGER, 0, 0, $02
	anim_wait 24
	anim_ret

BattleAnim_Wish:
	anim_2gfx BATTLE_ANIM_GFX_OBJECTS, BATTLE_ANIM_GFX_SHINE
	anim_bgp $1b
	anim_sound 0, 0, SFX_METRONOME
	anim_obj BATTLE_ANIM_OBJ_WISH_STAR, 0, 64, $4f
	anim_wait 96
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Ingrain:
	anim_2gfx BATTLE_ANIM_GFX_INGRAIN, BATTLE_ANIM_GFX_MEDIUM_BUBBLE
	anim_sound 0, 0, SFX_SCRATCH
	anim_extobj BATTLE_ANIM_EXT_OBJ_INGRAIN_ROOT, 48, 88, $0
	anim_wait 10
	anim_extobj BATTLE_ANIM_EXT_OBJ_INGRAIN_ROOT, 48, 88, $1
	anim_wait 10
	anim_sound 0, 0, SFX_SCRATCH
	anim_extobj BATTLE_ANIM_EXT_OBJ_INGRAIN_ROOT, 48, 88, $2
	anim_wait 10
	anim_extobj BATTLE_ANIM_EXT_OBJ_INGRAIN_ROOT, 48, 88, $3
	anim_wait 40
	anim_sound 0, 0, SFX_WATER_GUN
	anim_extobj BATTLE_ANIM_EXT_OBJ_INGRAIN_ORB, 48, 88, $0
	anim_wait 30
	anim_sound 0, 0, SFX_WATER_GUN
	anim_extobj BATTLE_ANIM_EXT_OBJ_INGRAIN_ORB, 48, 88, $1
	anim_wait 64
	anim_ret

BattleAnim_Superpower:
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $2, $0
	anim_call BattleAnimSub_FocusEnergy
	anim_wait 2
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_UserObj_1Row
	anim_bgp $1b
	anim_obp1 $1b
	anim_bgeffect BATTLE_BG_EFFECT_WOBBLE_MON, $0, BG_EFFECT_TARGET, $0
	anim_call BattleAnimSub_MegaPunchHits
	anim_incbgeffect BATTLE_BG_EFFECT_WOBBLE_MON
	anim_call BattleAnim_ShowMon_1
	anim_ret

BattleAnim_BrickBreak:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 48, $0
	anim_wait 16
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 148, 64, $0
	anim_wait 32
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 134, 56, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 134, 56, $0
	anim_wait 10
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Yawn:
	anim_2gfx BATTLE_ANIM_GFX_YAWN, BATTLE_ANIM_GFX_BUBBLE
	anim_sound 0, 0, SFX_KINESIS
	anim_extobj BATTLE_ANIM_EXT_OBJ_YAWN_CLOUD, 0, 0, $0
	anim_wait 76
	anim_sound 0, 1, SFX_TAIL_WHIP
	anim_wait 4
	anim_extobj BATTLE_ANIM_EXT_OBJ_YAWN_BUBBLE, 0, 0, $0
	anim_wait 8
	anim_extobj BATTLE_ANIM_EXT_OBJ_YAWN_BUBBLE, 0, 0, $1
	anim_wait 8
	anim_extobj BATTLE_ANIM_EXT_OBJ_YAWN_BUBBLE, 0, 0, $2
	anim_wait 12
	anim_wait 28
	anim_ret

BattleAnim_ArmThrust:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_KARATE_CHOP
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 134, 56, $0
	anim_wait 16
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_BlazeKick:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 144, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_call BattleAnimSub_Fire
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_KICK, 120, 64, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 64, $0
	anim_call BattleAnimSub_Fire
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnim_IceBall:
	anim_2gfx BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
	anim_icepal BATTLE_ANIM_ICE_PAL_LOAD
	anim_sound 6, 2, SFX_THROW_BALL
	anim_extobj BATTLE_ANIM_EXT_OBJ_ICE_BALL_PROJECTILE, 64, 92, $30
	anim_wait 36
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 4
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_ICE_BALL_CHIP, 136, 56, 4, $50, $dc, $68, $c8
	anim_wait 32
	anim_icepal BATTLE_ANIM_ICE_PAL_RESTORE
	anim_ret

BattleAnim_PoisonFang:
	anim_3gfx BATTLE_ANIM_GFX_CUT, BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_call BattleAnimSub_BiteJaws
	anim_wait 8
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $18
	anim_wait 16
	anim_sound 0, 1, SFX_BITE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 64, $18
	anim_call BattleAnimSub_PoisonBubblesEffect
	anim_wait 24
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_CrushClaw:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_call BattleAnim_Slash
	anim_sound 0, 1, SFX_CUT
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_RIGHT, 112, 40, $0
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_RIGHT, 116, 36, $0
	anim_wait 32
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_MeteorMash:
	anim_3gfx BATTLE_ANIM_GFX_FOCUS_PUNCH, BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_OBJECTS
	anim_sound 0, 1, SFX_TACKLE
	anim_extobj BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 144, 36, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 144, 40, $0
	anim_sound 0, 1, SFX_METRONOME
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR, 144, 40, 4, $2, $3, $4, $5
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $2
	anim_wait 18
	anim_sound 0, 1, SFX_TACKLE
	anim_extobj BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 120, 40, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 120, 44, $0
	anim_sound 0, 1, SFX_METRONOME
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR, 120, 44, 4, $2, $3, $4, $5
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $2
	anim_wait 18
	anim_sound 0, 1, SFX_TACKLE
	anim_extobj BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 144, 44, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 144, 48, $0
	anim_sound 0, 1, SFX_METRONOME
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR, 144, 48, 4, $2, $3, $4, $5
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $2
	anim_wait 18
	anim_sound 0, 1, SFX_TACKLE
	anim_extobj BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 120, 48, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 120, 52, $0
	anim_sound 0, 1, SFX_METRONOME
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR, 120, 52, 4, $2, $3, $4, $5
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $2
	anim_wait 18
	anim_sound 0, 1, SFX_TACKLE
	anim_extobj BATTLE_ANIM_EXT_OBJ_METEOR_MASH_FIST, 144, 52, $0
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 144, 56, $0
	anim_sound 0, 1, SFX_METRONOME
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_METEOR_MASH_STAR, 144, 56, 4, $2, $3, $4, $5
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $2
	anim_wait 20
	anim_ret

BattleAnim_Aromatherapy:
	anim_1gfx BATTLE_ANIM_GFX_PINK_PETAL
	anim_pinkpetalpal BATTLE_ANIM_PINK_PETAL_PAL_LOAD
	anim_sound 0, 0, SFX_MOONLIGHT
	anim_extobjlist BATTLE_ANIM_EXT_OBJ_AROMATHERAPY_PETAL, 7, 0, 88, $20, 8, 72, $32, 16, 56, $21, 24, 40, $33, 32, 28, $20, 40, 64, $31, 48, 80, $22
	anim_wait 16
	anim_extobjlist BATTLE_ANIM_EXT_OBJ_AROMATHERAPY_PETAL, 7, 4, 92, $33, 12, 34, $21, 20, 48, $30, 28, 60, $22, 36, 76, $33, 44, 44, $20, 52, 68, $31
	anim_wait 104
	anim_pinkpetalpal BATTLE_ANIM_PINK_PETAL_PAL_RESTORE
	anim_ret

BattleAnim_AirCutter:
	anim_3gfx BATTLE_ANIM_GFX_WHIP, BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_CUT
    anim_sound 3, 0, SFX_RAZOR_WIND
    anim_obj BATTLE_ANIM_OBJ_SONICBOOM_JP, 64, 64, $3
    anim_wait 8
    anim_sound 3, 0, SFX_RAZOR_WIND
    anim_obj BATTLE_ANIM_OBJ_SONICBOOM_JP, 64, 72, $3
    anim_wait 8
    anim_sound 3, 0, SFX_RAZOR_WIND
    anim_obj BATTLE_ANIM_OBJ_SONICBOOM_JP, 64, 80, $3
    anim_wait 8
    anim_sound 3, 0, SFX_RAZOR_WIND
    anim_obj BATTLE_ANIM_OBJ_SONICBOOM_JP, 64, 88, $3
    anim_wait 8
    anim_sound 3, 0, SFX_RAZOR_WIND
    anim_obj BATTLE_ANIM_OBJ_SONICBOOM_JP, 64, 96, $3
    anim_wait 40
    anim_incobjrange 1, 6
    anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
    anim_sound 0, 1, SFX_CUT
    anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
    anim_wait 48
    anim_ret

BattleAnim_Overheat:
	anim_2gfx BATTLE_ANIM_GFX_EMBER, BATTLE_ANIM_GFX_HAZE
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
	anim_bgeffect BATTLE_BG_EFFECT_FIRE_BGPALS, $0, $0, $3c
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $0
	anim_sound 0, 0, SFX_EMBER
	anim_objparams BATTLE_ANIM_OBJ_OVERHEAT_FLAME, 48, 96, 9, $0, $1, $2, $3, $4, $5, $6, $7, $8
	anim_wait 80
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_call BattleAnim_UserObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_VIBRATE_MON, $0, BG_EFFECT_TARGET, $0
.loop
	anim_obj BATTLE_ANIM_OBJ_SMOKE, 48, 96, $20
	anim_wait 8
	anim_loop 3, .loop
	anim_call BattleAnim_ShowMon_1
	anim_wait 128
	anim_ret

BattleAnim_RockTomb:
	anim_1gfx BATTLE_ANIM_GFX_ROCKS
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $0
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 128, 64, $40
	anim_wait 12
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 120, 68, $30
	anim_wait 12
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 152, 68, $30
	anim_wait 12
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 144, 64, $40
	anim_wait 12
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_BIG_ROCK, 136, 68, $30
	anim_wait 56
	anim_ret

BattleAnim_SilverWind:
	anim_1gfx BATTLE_ANIM_GFX_SILVER_WIND
	anim_silverwindpal BATTLE_ANIM_SILVER_WIND_PAL_LOAD
	anim_call BattleAnimSub_SilverWind
	anim_silverwindpal BATTLE_ANIM_SILVER_WIND_PAL_RESTORE
	anim_ret

BattleAnim_ShadowPunch:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_GHOST_FLAME
	anim_ghostflamepal BATTLE_ANIM_GHOST_FLAME_PAL_LOAD
	anim_sound 0, 0, SFX_CURSE
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_WHITE_WAIT_FADE_BACK, $0, BG_EFFECT_USER, $80
	anim_wait 96
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 56, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_call BattleAnimSub_GhostFlame
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_WHITE_WAIT_FADE_BACK
	anim_wait 4
	anim_ghostflamepal BATTLE_ANIM_GHOST_FLAME_PAL_RESTORE
	anim_ret

BattleAnim_SignalBeam:
	anim_1gfx BATTLE_ANIM_GFX_SIGNAL_BEAM
	anim_signalpal BATTLE_ANIM_SIGNAL_BEAM_PAL_LOAD
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_sound 0, 0, SFX_KINESIS
.loop1
	anim_extobj BATTLE_ANIM_EXT_OBJ_SIGNAL_BEAM_RING, 64, 92, $0
	anim_wait 4
	anim_sound 0, 1, SFX_KINESIS
	anim_loop 8, .loop1
.loop2
	anim_extobj BATTLE_ANIM_EXT_OBJ_SIGNAL_BEAM_RING, 64, 92, $0
	anim_wait 4
	anim_sound 0, 1, SFX_KINESIS
	anim_loop 16, .loop2
	anim_wait 48
	anim_signalpal BATTLE_ANIM_SIGNAL_BEAM_PAL_RESTORE
	anim_ret

BattleAnimSub_SilverWind:
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SILVER_WIND, 24, 64, $3
	anim_wait 6
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SILVER_WIND, 24, 64, $7
	anim_wait 6
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SILVER_WIND, 24, 64, $6
	anim_wait 6
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SILVER_WIND, 24, 64, $2
	anim_wait 6
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SILVER_WIND, 24, 64, $4
	anim_wait 6
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SILVER_WIND, 24, 64, $0
	anim_wait 6
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SILVER_WIND, 24, 64, $5
	anim_wait 6
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SILVER_WIND, 24, 64, $1
	anim_wait 74
	anim_ret

BattleAnim_Extrasensory:
    anim_1gfx BATTLE_ANIM_GFX_SHINE
    anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
    anim_sound 0, 0, SFX_FORESIGHT
    anim_obj BATTLE_ANIM_OBJ_FORESIGHT, 64, 88, $0
    anim_wait 24
    anim_sound 0, 1, SFX_PSYCHIC
    anim_bgeffect BATTLE_BG_EFFECT_WHIRLPOOL, $0, $0, $0
    anim_wait 128
    anim_incbgeffect BATTLE_BG_EFFECT_WHIRLPOOL
    anim_ret

BattleAnim_SkyUppercut:
	anim_2gfx BATTLE_ANIM_GFX_SPEED, BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
.loop	
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 12, 0, $c7
	anim_wait 12
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 28, 0, $c7
	anim_wait 12
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 20, 0, $c7
	anim_wait 12
	anim_loop 2, .loop
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 12, 0, $c7
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 6
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 64, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 64, $0
	anim_wait 3
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 3
	anim_obj BATTLE_ANIM_OBJ_SEISMIC_TOSS_LIGHT, 28, 0, $c7
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 48, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_wait 3
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 40, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 40, $0
	anim_wait 3
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 32, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 32, $0
	anim_wait 8
	anim_call BattleAnim_ShowMon_0
	anim_wait 12
	anim_ret

BattleAnim_SandTomb:
	anim_1gfx BATTLE_ANIM_GFX_SAND_TOMB_FLECK
	anim_call BattleAnim_UserObj_1Row
.loop
	anim_sound 0, 1, SFX_SANDSTORM
	anim_extobj BATTLE_ANIM_EXT_OBJ_SAND_TOMB_FLECK, 136, 56, $00
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_VIBRATE_MON, $0, BG_EFFECT_TARGET, $0
	anim_loop 8, .loop
	anim_wait 96
	anim_call BattleAnim_ShowMon_1
	anim_ret

BattleAnim_BulletSeed:
	anim_2gfx BATTLE_ANIM_GFX_BULLET_SEED, BATTLE_ANIM_GFX_HIT
	anim_sound 6, 2, SFX_THROW_BALL
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $04
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $14
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $24
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $34
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $04
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $14
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $24
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $34
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $04
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_BULLET_SEED, 56, 96, $14
	anim_wait 40
	anim_ret

BattleAnim_AerialAce:
	anim_2gfx BATTLE_ANIM_GFX_WIND, BATTLE_ANIM_GFX_CUT
	anim_call BattleAnim_TargetObj_1Row
	anim_call BattleAnimSub_AgilityWindLines
.loop
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_wait 4
	anim_loop 18, .loop
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 12
	anim_sound 0, 1, SFX_CUT
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
	anim_wait 32
	anim_call BattleAnim_ShowMon_0
	anim_wait 4
	anim_ret

BattleAnim_Block:
	anim_1gfx BATTLE_ANIM_GFX_BLOCK
	anim_sound 0, 1, SFX_KINESIS_2
	anim_extobj BATTLE_ANIM_EXT_OBJ_BLOCK_X, 136, 56, $0
	anim_wait 96
	anim_ret

BattleAnim_Howl:
	anim_1gfx BATTLE_ANIM_GFX_NOISE
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_wait 12
	anim_cry $2
	anim_call BattleAnimSub_Sound
	anim_wait 15
	anim_call BattleAnimSub_Sound
	anim_wait 30
	anim_ret

BattleAnim_DragonClaw:
	anim_2gfx BATTLE_ANIM_GFX_EMBER, BATTLE_ANIM_GFX_DRAGON_CLAW
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_LOAD
.loop
	anim_sound 0, 0, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FLAME_WHEEL, 48, 96, $0
	anim_wait 6
	anim_loop 8, .loop
	anim_wait 96
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_RESTORE
	anim_dragonclawpal BATTLE_ANIM_DRAGON_CLAW_PAL_LOAD
	anim_dragonbluepal BATTLE_ANIM_DRAGON_BLUE_PAL_LOAD
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_SLASH, 126, 46, $0
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_SLASH, 126, 66, $0
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_SLASH_XFLIP, 146, 46, $0
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_SLASH_XFLIP, 146, 66, $0
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_wait 20
	anim_call BattleAnimSub_DragonClawTrailDownRight
	anim_wait 15
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_wait 20
	anim_call BattleAnimSub_DragonClawTrailDownLeft
	anim_wait 21
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 5
	anim_incobj 5
	anim_wait 1
	anim_dragonclawpal BATTLE_ANIM_DRAGON_CLAW_PAL_RESTORE
	anim_dragonbluepal BATTLE_ANIM_DRAGON_BLUE_PAL_RESTORE
	anim_ret

BattleAnimSub_DragonClawTrailDownRight:
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_FLAME, 126, 44, $0
	anim_wait 3
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_FLAME, 136, 56, $1
	anim_wait 3
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_FLAME, 146, 68, $2
	anim_ret

BattleAnimSub_DragonClawTrailDownLeft:
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_FLAME, 146, 44, $3
	anim_wait 3
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_FLAME, 136, 56, $4
	anim_wait 3
	anim_obj BATTLE_ANIM_OBJ_DRAGON_CLAW_FLAME, 126, 68, $5
	anim_ret

BattleAnimSub_ShadowClawTrailDownLeft:
	anim_extobj BATTLE_ANIM_EXT_OBJ_SHADOW_CLAW_FLAME, 146, 44, $3
	anim_wait 3
	anim_extobj BATTLE_ANIM_EXT_OBJ_SHADOW_CLAW_FLAME, 136, 56, $4
	anim_wait 3
	anim_extobj BATTLE_ANIM_EXT_OBJ_SHADOW_CLAW_FLAME, 126, 68, $5
	anim_ret

BattleAnim_BulkUp:
	anim_2gfx BATTLE_ANIM_GFX_WIND, BATTLE_ANIM_GFX_SPEED
.loop
	anim_sound 0, 0, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_SWAGGER, 72, 88, $44
	anim_wait 32
	anim_loop 2, .loop
.loop2
	anim_call BattleAnimSub_BulkUpFocusEnergyBurst
	anim_loop 3, .loop2
	anim_wait 16
	anim_ret

BattleAnimSub_BulkUpFocusEnergyBurst:
	anim_sound 0, 0, SFX_SWORDS_DANCE
	anim_extobj BATTLE_ANIM_EXT_OBJ_BULK_UP_FOCUS, 44, 108, $6
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_BULK_UP_FOCUS, 36, 108, $6
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_BULK_UP_FOCUS, 52, 108, $8
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_BULK_UP_FOCUS, 28, 108, $8
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_BULK_UP_FOCUS, 60, 108, $6
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_BULK_UP_FOCUS, 20, 108, $8
	anim_wait 2
	anim_extobj BATTLE_ANIM_EXT_OBJ_BULK_UP_FOCUS, 68, 108, $8
	anim_wait 2
	anim_ret

BattleAnim_MudShot:
	anim_1gfx BATTLE_ANIM_GFX_MUD_BALL_MEDIUM
	anim_groundpal BATTLE_ANIM_GROUND_PAL_LOAD
	anim_sound 6, 2, SFX_SLUDGE_BOMB
	anim_obj BATTLE_ANIM_OBJ_MUD_BALL_MEDIUM, 64, 94, $10
	anim_wait 12
	anim_sound 6, 2, SFX_SLUDGE_BOMB
	anim_obj BATTLE_ANIM_OBJ_MUD_BALL_MEDIUM, 76, 78, $14
	anim_wait 12
	anim_sound 6, 2, SFX_SLUDGE_BOMB
	anim_obj BATTLE_ANIM_OBJ_MUD_BALL_MEDIUM, 52, 86, $0c
	anim_wait 8
	anim_sound 0, 1, SFX_WATER_GUN
	anim_wait 12
	anim_sound 0, 1, SFX_WATER_GUN
	anim_wait 12
	anim_sound 0, 1, SFX_WATER_GUN
	anim_wait 28
	anim_groundpal BATTLE_ANIM_GROUND_PAL_RESTORE
	anim_ret

BattleAnim_PoisonTail:
	anim_3gfx BATTLE_ANIM_GFX_REFLECT, BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_obp0 $0
	anim_call BattleAnimSub_PoisonMetallic
	anim_call BattleAnim_TargetObj_1Row
	anim_resetobp0
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 6
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 8
	anim_call BattleAnim_ShowMon_0
	anim_call BattleAnimSub_PoisonBubblesEffect
	anim_wait 24
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_VoltTackle:
	anim_1gfx BATTLE_ANIM_GFX_CHARGE
	anim_sound 0, 0, SFX_CHARGE
	anim_extobj BATTLE_ANIM_EXT_OBJ_VOLT_TACKLE_CHARGE_CENTER, 48, 84, $0
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_SHOCK_WAVE_CHARGE, 48, 84, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 104
	anim_clearobjs
	anim_wait 4

	anim_2gfx BATTLE_ANIM_GFX_THUNDERSHOCK_HORIZONTAL, BATTLE_ANIM_GFX_HIT
	anim_clearhuds
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_extobj BATTLE_ANIM_EXT_OBJ_VOLT_TACKLE_BOLT, 0, 0, $0
	anim_wait 17
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_extobj BATTLE_ANIM_EXT_OBJ_VOLT_TACKLE_BOLT, 0, 0, $1
	anim_wait 17
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_extobj BATTLE_ANIM_EXT_OBJ_VOLT_TACKLE_BOLT, 0, 0, $2
	anim_wait 17
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_extobj BATTLE_ANIM_EXT_OBJ_VOLT_TACKLE_BOLT, 0, 0, $3
	anim_wait 17
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_extobj BATTLE_ANIM_EXT_OBJ_VOLT_TACKLE_BOLT, 0, 0, $4
	anim_wait 17
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 8

	anim_2gfx BATTLE_ANIM_GFX_ELECTRICITY_EFFECT, BATTLE_ANIM_GFX_THUNDERBOLT_AFTEREFFECT
	anim_thunderboltpal BATTLE_ANIM_THUNDERBOLT_PAL_LOAD
	anim_call BattleAnimSub_ThunderboltAftereffect
	anim_call BattleAnimSub_ElectricityEffect
	anim_thunderboltpal BATTLE_ANIM_THUNDERBOLT_PAL_RESTORE
	anim_wait 4
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 16
	anim_sound 0, 0, SFX_ZAP_CANNON
	anim_call BattleAnimSub_ElectricityEffectUser
	anim_wait 8
	anim_ret

BattleAnim_MagicalLeaf:
	anim_2gfx BATTLE_ANIM_GFX_PLANT, BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_GREEN_OBPAL, $0, $0, $20
	anim_sound 0, 0, SFX_METRONOME
	anim_objparams BATTLE_ANIM_OBJ_RAZOR_LEAF, 48, 80, 6, $28, $5c, $10, $e8, $9c, $d0
	anim_wait 6
	anim_objparams BATTLE_ANIM_OBJ_RAZOR_LEAF, 48, 80, 4, $1c, $50, $dc, $90
	anim_wait 80
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 3
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 5
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 7
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 9
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 1
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 2
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 4
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 6
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 8
	anim_wait 2
	anim_sound 16, 2, SFX_SHINE
	anim_incobj 10
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_CYCLE_GREEN_OBPAL
	anim_ret

BattleAnim_CalmMind:
	anim_1gfx BATTLE_ANIM_GFX_MISC
	anim_bgp $1b
	anim_sound 6, 1, SFX_FLASH
.loop
	anim_objparams BATTLE_ANIM_OBJ_MIND_READER, 48, 88, 4, $3, $12, $20, $31
	anim_wait 16
	anim_loop 2, .loop
	anim_wait 32
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_DragonDance:
	anim_2gfx BATTLE_ANIM_GFX_CHARGE, BATTLE_ANIM_GFX_ELECTRICITY_EFFECT
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_LOAD
	anim_sound 0, 0, SFX_SWORDS_DANCE
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_DRAGON_DANCE_ORB, 48, 80, 6, $00, $0b, $15, $20, $2b, $35
	anim_call BattleAnimSub_ElectricityEffectUser
	anim_sound 0, 0, SFX_WARP_TO
	anim_wait 30
	anim_sound 0, 0, SFX_WARP_TO
	anim_wait 52
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_RESTORE
	anim_ret

BattleAnim_RockBlast:
	anim_2gfx BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_SPARK
	anim_extobj BATTLE_ANIM_EXT_OBJ_ROCK_BLAST, 56, 88, $4
	anim_wait 20
	anim_sound 0, 1, SFX_STRENGTH
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $1, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_ROCK_BLAST_CHIP, 136, 56, 4, $2, $3, $4, $5
	anim_call BattleAnim_ShowMon_0
	anim_wait 24
	anim_ret

BattleAnim_ShockWave:
	anim_3gfx BATTLE_ANIM_GFX_CHARGE, BATTLE_ANIM_GFX_ELECTRICITY_EFFECT, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_CHARGE
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_SHOCK_WAVE_CHARGE, 48, 84, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 100
	anim_clearobjs
	anim_wait 4
	anim_sound 0, 0, SFX_ZAP_CANNON
	anim_call BattleAnimSub_ElectricityEffectUser
	anim_wait 8
	anim_sound 0, 0, SFX_SWORDS_DANCE
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_SHOCK_WAVE_ORB, 48, 84, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 22
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 6
	anim_sound 0, 0, SFX_THUNDERSHOCK_SHORT
	anim_call BattleAnimSub_ElectricityEffect
	anim_wait 16
	anim_ret

BattleAnimSub_WaterPulseUserBubbles:
	anim_objlist BATTLE_ANIM_OBJ_WATER_PULSE_DRIFT_BUBBLE, 5, 64, 88, $0, 16, 88, $1, 136, 72, $2, 52, 56, $3, 96, 88, $4
	anim_ret

BattleAnim_WaterPulse:
	anim_3gfx BATTLE_ANIM_GFX_PSYCHIC, BATTLE_ANIM_GFX_SMALL_BUBBLE, BATTLE_ANIM_GFX_TINY_BUBBLE
	anim_waterpal BATTLE_ANIM_WATER_PAL_LOAD
	anim_bgeffect BATTLE_BG_EFFECT_WHIRLPOOL, $0, $0, $0
	anim_sound 6, 2, SFX_BUBBLEBEAM
	anim_wait 10
	anim_call BattleAnimSub_WaterPulseUserBubbles
	anim_wait 50

	anim_sound 0, 1, SFX_BUBBLEBEAM
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_RING, 64, 92, $2
	anim_wait 5
	anim_sound 0, 1, SFX_BUBBLEBEAM
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_RING, 64, 92, $2
	anim_wait 5
	anim_sound 0, 1, SFX_BUBBLEBEAM
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_RING, 64, 92, $2

	;anim_wait 5
	; Ring-path bubbles. These approximate Emerald's ring-spawned bubbles.
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 90, 69, $82
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 98, 85, $83
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 96, 70, $80
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 90, 84, $81
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 92, 68, $82
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 100, 83, $83
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 120, 47, $82
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 128, 77, $83
	anim_wait 5
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $1, $0
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 126, 49, $80
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 118, 76, $81
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 120, 64, $0
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 148, 60, $1
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 122, 46, $82
	anim_obj BATTLE_ANIM_OBJ_WATER_PULSE_PATH_BUBBLE, 130, 78, $83
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 128, 48, $2
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 156, 52, $3
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 116, 40, $0
	anim_obj BATTLE_ANIM_OBJ_WATERFALL_BUBBLE, 144, 36, $1
	anim_wait 28
	anim_incbgeffect BATTLE_BG_EFFECT_WHIRLPOOL
	anim_wait 8
	anim_waterpal BATTLE_ANIM_WATER_PAL_RESTORE
	anim_ret

BattleAnim_Pluck:
	anim_2gfx BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
.loop
	anim_sound 0, 1, SFX_PECK
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 128, 48, $0
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 128, 48, 2, $50, $dc
	anim_wait 8
	anim_sound 0, 1, SFX_PECK
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 136, 56, $0
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 136, 56, 2, $68, $c8
	anim_wait 12
	anim_loop 3, .loop
	anim_wait 16
	anim_ret

BattleAnim_SuckerPunch:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_CURSE
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_WHITE_WAIT_FADE_BACK, $0, BG_EFFECT_USER, $80
	anim_wait 72
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_WHITE_WAIT_FADE_BACK
	anim_wait 20
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $f, $2
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 144, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_wait 4
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 120, 64, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 64, $0
	anim_wait 24
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 8
	anim_ret

BattleAnim_ForcePalm:
	anim_2gfx BATTLE_ANIM_GFX_FORCE_PALM, BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_UserObj_1Row
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_extobj BATTLE_ANIM_EXT_OBJ_FORCE_PALM, 72, 56, $0
	anim_wait 8
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_bgeffect BATTLE_BG_EFFECT_VIBRATE_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 34
	anim_call BattleAnim_ShowMon_1
	anim_ret

BattleAnim_PoisonJab:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_sound 6, 2, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH_SHAKE, 136, 56, $43
	anim_wait 3
	anim_call BattleAnimSub_PoisonBubblesEffect
	anim_wait 24
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_NightSlash:
	anim_2gfx BATTLE_ANIM_GFX_SHINE, BATTLE_ANIM_GFX_CUT
	anim_bgp $1b
	anim_sound 0, 1, SFX_CUT
	anim_extobj BATTLE_ANIM_EXT_OBJ_GLIMMER_YFIX, 150, 38, $0
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 148, 36, $0
	anim_wait 32
	anim_sound 0, 1, SFX_CUT
	anim_extobj BATTLE_ANIM_EXT_OBJ_GLIMMER_YFIX, 118, 70, $0
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $2
	anim_extobj BATTLE_ANIM_EXT_OBJ_CUT_LONG_UP_RIGHT, 120, 72, $0
	anim_extobj BATTLE_ANIM_EXT_OBJ_CUT_LONG_UP_RIGHT, 116, 68, $0
	anim_wait 40
	anim_ret

BattleAnim_XScissor:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_bugpal BATTLE_ANIM_BUG_PAL_LOAD
	anim_sound 0, 1, SFX_CUT
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_RIGHT, 120, 36, $0
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 150, 36, $0
	anim_wait 24
	anim_bugpal BATTLE_ANIM_BUG_PAL_RESTORE
	anim_ret

BattleAnim_DrainPunch:
	anim_2gfx BATTLE_ANIM_GFX_CHARGE, BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MONS_TO_BLACK_REPEATING, $0, BG_EFFECT_TARGET, $10
	anim_setvar $0
.loop
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_PUNCH_SHAKE, 136, 56, $43
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 128, 48, $2
	anim_wait 6
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 136, 64, $3
	anim_wait 6
	anim_sound 6, 3, SFX_WATER_GUN
	anim_obj BATTLE_ANIM_OBJ_ABSORB, 136, 32, $4
	anim_wait 6
	anim_incvar
	anim_if_var_equal $7, .done
	anim_if_var_equal $2, .spawn
	anim_jump .loop

.spawn
	anim_obj BATTLE_ANIM_OBJ_ABSORB_CENTER, 44, 88, $0
	anim_jump .loop

.done
	anim_wait 32
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MONS_TO_BLACK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_EnergyBall:
	anim_4gfx BATTLE_ANIM_GFX_CHARGE, BATTLE_ANIM_GFX_EGG, BATTLE_ANIM_GFX_SMOKE, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_CHARGE
	anim_obj BATTLE_ANIM_OBJ_ABSORB_CENTER, 48, 84, $0
	anim_objparams BATTLE_ANIM_OBJ_SOLAR_BEAM_CHARGE, 48, 84, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 104
	anim_sound 6, 2, SFX_VINE_WHIP
	anim_obj BATTLE_ANIM_OBJ_ENERGY_BALL, 64, 92, $4
	anim_wait 16
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 132, 56, $0
	anim_wait 8
	anim_ret

BattleAnim_BulletPunch:
	anim_1gfx BATTLE_ANIM_GFX_REFLECT
	anim_obp0 $0
	anim_sound 0, 0, SFX_RAGE
	anim_call BattleAnim_TargetObj_1Row
	anim_call BattleAnimSub_Metallic
	anim_call BattleAnim_ShowMon_0
	anim_2gfx BATTLE_ANIM_GFX_SPEED, BATTLE_ANIM_GFX_HIT
	anim_resetobp0
	anim_sound 0, 0, SFX_MENU
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_call BattleAnimSub_SpeedLineBurst
.loop
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 144, 48, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $0
	anim_wait 4
	anim_loop 4, .loop
	anim_wait 8
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_ret

BattleAnim_ShadowClaw:
	anim_2gfx BATTLE_ANIM_GFX_CUT, BATTLE_ANIM_GFX_GHOST_FLAME
	anim_ghostflamepal BATTLE_ANIM_GHOST_FLAME_PAL_LOAD
	anim_sound 0, 1, SFX_CUT
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 148, 36, $0
	anim_wait 20
	anim_call BattleAnimSub_ShadowClawTrailDownLeft
	anim_wait 20
	anim_clearobjs
	anim_wait 8
	anim_ghostflamepal BATTLE_ANIM_GHOST_FLAME_PAL_RESTORE
	anim_ret

BattleAnim_ThunderFang:
	anim_3gfx BATTLE_ANIM_GFX_CUT, BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_ELECTRICITY_EFFECT
	anim_call BattleAnimSub_BiteJaws
	anim_wait 8
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $18
	anim_wait 16
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 64, $18
	anim_wait 2
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $2
	anim_sound 0, 1, SFX_THUNDERSHOCK_SHORT
	anim_call BattleAnimSub_ElectricityEffect
	anim_wait 12
	anim_ret

BattleAnim_IceFang:
	anim_3gfx BATTLE_ANIM_GFX_CUT, BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_ICE
	anim_call BattleAnimSub_BiteJaws
	anim_wait 8
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $18
	anim_wait 16
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 64, $18
	anim_call BattleAnimSub_Ice
	anim_wait 12
	anim_ret

BattleAnim_FireFang:
	anim_3gfx BATTLE_ANIM_GFX_CUT, BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_EMBER
	anim_call BattleAnimSub_BiteJaws
	anim_wait 8
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 48, $18
	anim_wait 16
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 64, $18
	anim_sound 0, 1, SFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
	anim_call BattleAnimSub_Fire
	anim_wait 12
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnim_MudBomb:
	anim_2gfx BATTLE_ANIM_GFX_SLUDGE_BOMB, BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_groundpal BATTLE_ANIM_GROUND_PAL_LOAD
	anim_sound 6, 2, SFX_SLUDGE_BOMB
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_PROJECTILE, 64, 92, $18
	anim_wait 38
	anim_call BattleAnimSub_MudBombSplatter
	anim_wait 16
	anim_clearobjs
	anim_groundpal BATTLE_ANIM_GROUND_PAL_RESTORE
	anim_ret

BattleAnimSub_MudBombSplatter:
	anim_sound 0, 1, SFX_TOXIC
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_SPLATTER, 132, 36, $0
	anim_wait 4
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_SPLATTER, 120, 40, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TOXIC
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_SPLATTER, 144, 44, $0
	anim_wait 4
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_SPLATTER, 126, 49, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TOXIC
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_SPLATTER, 140, 53, $0
	anim_wait 4
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_SPLATTER, 118, 57, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TOXIC
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_SPLATTER, 146, 61, $0
	anim_wait 4
	anim_extobj BATTLE_ANIM_EXT_OBJ_MUD_BOMB_SPLATTER, 134, 65, $0
	anim_wait 4
	anim_ret

BattleAnim_LavaPlume:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_firepal BATTLE_ANIM_FIRE_PAL_LOAD
.loop1
	anim_sound 0, 0, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FLAME_WHEEL, 48, 96, $0
	anim_wait 6
	anim_loop 8, .loop1
	anim_wait 12
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $0
.loop2
	anim_sound 0, 1, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_LAVA_PLUME_ERUPTION, 48, 92, $1
	anim_wait 16
	anim_loop 5, .loop2
	anim_wait 84
	anim_firepal BATTLE_ANIM_FIRE_PAL_RESTORE
	anim_ret

BattleAnim_StoneEdge:
	anim_2gfx BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $1, $0
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_STONE_EDGE_ROCK, 148, 60, $3
	anim_wait 8
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_STONE_EDGE_ROCK, 124, 60, $1
	anim_wait 8
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_STONE_EDGE_ROCK, 136, 64, $5
	anim_wait 8
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_STONE_EDGE_ROCK, 112, 56, $0
	anim_wait 8
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_STONE_EDGE_ROCK, 160, 56, $4
	anim_wait 8
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_STONE_EDGE_ROCK, 136, 58, $2
	anim_wait 32
	anim_ret

BattleAnim_BugBite:
	anim_2gfx BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
.loop
	anim_sound 0, 1, SFX_HEADBUTT
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 128, 48, $0
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 128, 48, 2, $50, $dc
	anim_wait 8
	anim_sound 0, 1, SFX_HEADBUTT
	anim_obj BATTLE_ANIM_OBJ_HIT_SMALL_YFIX, 136, 56, $0
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 136, 56, 2, $68, $c8
	anim_wait 12
	anim_loop 5, .loop
	anim_wait 16
	anim_ret

BattleAnim_SludgeWave:
	anim_1gfx BATTLE_ANIM_GFX_POISON_BUBBLE
	anim_poisonpal BATTLE_ANIM_POISON_PAL_LOAD
	anim_call BattleAnimSub_PoisonSludgeArc
	anim_call BattleAnimSub_PoisonSplatter
	anim_wait 16
	anim_clearobjs
	anim_call BattleAnimSub_PoisonBubblesEffect
	anim_wait 24
	anim_poisonpal BATTLE_ANIM_POISON_PAL_RESTORE
	anim_ret

BattleAnim_Hex:
	anim_2gfx BATTLE_ANIM_GFX_PSYCHIC, BATTLE_ANIM_GFX_GHOST_FLAME
	anim_ghostflamepal BATTLE_ANIM_GHOST_FLAME_PAL_LOAD
	anim_sound 0, 1, SFX_MEAN_LOOK
	anim_extobj BATTLE_ANIM_EXT_OBJ_HEX_MEAN_LOOK, 132, 48, $0
	anim_wait 16
	anim_sound 0, 1, SFX_BURN
	anim_extobj BATTLE_ANIM_EXT_OBJ_HEX_GHOST_FLAME, 132, 48, $00
	anim_wait 16
	anim_extobj BATTLE_ANIM_EXT_OBJ_HEX_GHOST_FLAME, 132, 48, $00
	anim_wait 16
	anim_extobj BATTLE_ANIM_EXT_OBJ_HEX_GHOST_FLAME, 132, 48, $00
	anim_wait 16
	anim_extobj BATTLE_ANIM_EXT_OBJ_HEX_GHOST_FLAME, 132, 48, $00
	anim_wait 68
	anim_sound 0, 1, SFX_CURSE
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $2
	anim_wait 12
	anim_clearobjs
	anim_wait 8
	anim_ghostflamepal BATTLE_ANIM_GHOST_FLAME_PAL_RESTORE
	anim_ret

BattleAnim_WildCharge:
	anim_3gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_CHARGE, BATTLE_ANIM_GFX_LIGHTNING
	anim_sound 0, 0, SFX_CHARGE
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_SHOCK_WAVE_CHARGE, 48, 84, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_wait 100
	anim_clearobjs
	anim_wait 4

	anim_sound 0, 0, SFX_ZAP_CANNON
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $4, $3
	anim_obj BATTLE_ANIM_OBJ_THUNDER_WAVE, 48, 92, $0
	anim_wait 24
	anim_setobj $9, $3
	anim_wait 1

	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 0, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 48, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 4
	anim_incobj $a
	anim_wait 1

	anim_2gfx BATTLE_ANIM_GFX_ELECTRICITY_EFFECT, BATTLE_ANIM_GFX_THUNDERBOLT_AFTEREFFECT
	anim_thunderboltpal BATTLE_ANIM_THUNDERBOLT_PAL_LOAD
	anim_call BattleAnimSub_ThunderboltAftereffect
	anim_call BattleAnimSub_ElectricityEffect
	anim_thunderboltpal BATTLE_ANIM_THUNDERBOLT_PAL_RESTORE
	anim_wait 4
	anim_ret

BattleAnim_DrillRun:
	anim_3gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_WIND, BATTLE_ANIM_GFX_HIT
	anim_obp0 $e4
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HORN, 72, 80, $1
	anim_wait 8
	anim_call BattleAnim_ShowMon_0
	anim_wait 4
	anim_call BattleAnimSub_DrillRunSpinHit
	anim_call BattleAnimSub_DrillRunSpinHit
	anim_call BattleAnimSub_DrillRunSpinHit
	anim_wait 20
	anim_clearobjs
	anim_resetobp0
	anim_ret

BattleAnimSub_DrillRunSpinHit:
.loop
	anim_sound 0, 0, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_RAPID_SPIN, 44, 112, $0
	anim_wait 2
	anim_loop 5, .loop
	anim_wait 8
	anim_sound 0, 1, SFX_MEGA_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $0
	anim_wait 14
	anim_ret

BattleAnim_IcicleCrash:
	anim_1gfx BATTLE_ANIM_GFX_ICE_CHUNK
	anim_icepal BATTLE_ANIM_ICE_PAL_LOAD
	anim_obj BATTLE_ANIM_OBJ_ICE_CHUNK, 136, 64, $0
	anim_wait 12
	anim_obj BATTLE_ANIM_OBJ_ICE_CHUNK, 120, 68, $0
	anim_wait 6
	anim_sound 0, 1, SFX_STRENGTH
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $0
	anim_wait 12
	anim_sound 0, 1, SFX_STRENGTH
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $0
	anim_obj BATTLE_ANIM_OBJ_ICE_CHUNK, 152, 68, $0
	anim_wait 18
	anim_sound 0, 1, SFX_STRENGTH
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $0
	anim_wait 20
	anim_icepal BATTLE_ANIM_ICE_PAL_RESTORE
	anim_ret

BattleAnim_GigaDrain:
	anim_2gfx BATTLE_ANIM_GFX_BUBBLE, BATTLE_ANIM_GFX_CHARGE
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MONS_TO_BLACK_REPEATING, $0, BG_EFFECT_TARGET, $10
	anim_sound 6, 3, SFX_GIGA_DRAIN
	anim_call BattleAnimSub_Drain
	anim_wait 176
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MONS_TO_BLACK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_wait 1
	anim_1gfx BATTLE_ANIM_GFX_SHINE
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
.loop
	anim_sound 0, 0, SFX_METRONOME
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 24, 64, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 56, 104, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 24, 104, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 56, 64, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 40, 84, $0
	anim_wait 5
	anim_loop 2, .loop
	anim_wait 32
	anim_ret

BattleAnim_Endure:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING, $0, BG_EFFECT_USER, $20
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
.loop
	anim_call BattleAnimSub_FocusEnergyBurst
	anim_loop 5, .loop
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Charm:
	anim_1gfx BATTLE_ANIM_GFX_OBJECTS
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_WOBBLE_MON, $0, BG_EFFECT_USER, $0
	anim_sound 0, 0, SFX_ATTRACT
	anim_obj BATTLE_ANIM_OBJ_HEART, 64, 80, $0
	anim_wait 32
	anim_incbgeffect BATTLE_BG_EFFECT_WOBBLE_MON
	anim_call BattleAnim_ShowMon_0
	anim_wait 4
	anim_ret

BattleAnim_Rollout:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_SPARK
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_ROLLOUT, $60, $1, $1
	anim_bgeffect BATTLE_BG_EFFECT_BODY_SLAM, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG, 136, 40, $0
	anim_wait 8
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_FalseSwipe:
	anim_2gfx BATTLE_ANIM_GFX_SHINE, BATTLE_ANIM_GFX_CUT
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
	anim_sound 0, 1, SFX_CUT
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 136, 40, $0
	anim_wait 32
	anim_ret

BattleAnim_Swagger:
	anim_2gfx BATTLE_ANIM_GFX_MISC, BATTLE_ANIM_GFX_WIND
.loop
	anim_sound 0, 0, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_SWAGGER, 72, 88, $44
	anim_wait 32
	anim_loop 2, .loop
	anim_wait 32
	anim_sound 0, 1, SFX_KINESIS_2
	anim_obj BATTLE_ANIM_OBJ_ANGER, 104, 40, $0
	anim_wait 40
	anim_ret

BattleAnim_MilkDrink:
	anim_2gfx BATTLE_ANIM_GFX_MISC, BATTLE_ANIM_GFX_BUBBLE
	anim_call BattleAnim_TargetObj_1Row
	anim_obj BATTLE_ANIM_OBJ_MILK_DRINK, 74, 104, $0
	anim_wait 16
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING, $0, BG_EFFECT_USER, $40
	anim_sound 0, 0, SFX_MILK_DRINK
.loop
	anim_obj BATTLE_ANIM_OBJ_RECOVER, 44, 88, $20
	anim_wait 8
	anim_loop 8, .loop
	anim_wait 128
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Spark:
	anim_2gfx BATTLE_ANIM_GFX_ELECTRICITY_EFFECT, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_ZAP_CANNON
	anim_call BattleAnimSub_ElectricityEffectUser
	anim_wait 1
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_sound 0, 0, SFX_SPARK
	anim_wait 16
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 4
	anim_incobj $d
	anim_wait 1
	anim_sound 0, 1, SFX_THUNDERSHOCK_SHORT
	anim_call BattleAnimSub_ElectricityEffect
	anim_ret

BattleAnim_FuryCutter:
	anim_1gfx BATTLE_ANIM_GFX_CUT
.loop
	anim_sound 0, 1, SFX_CUT
	anim_if_param_and %00000001, .obj1
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
	anim_jump .okay

.obj1
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_RIGHT, 112, 40, $0
.okay
	anim_wait 16
	anim_jumpuntil .loop
	anim_ret

BattleAnim_SteelWing:
	anim_1gfx BATTLE_ANIM_GFX_REFLECT
	anim_obp0 $0
	anim_sound 0, 0, SFX_RAGE
	anim_call BattleAnim_TargetObj_1Row
	anim_call BattleAnimSub_Metallic
	anim_call BattleAnim_ShowMon_0
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_resetobp0
	anim_call BattleAnimSub_WingAttackHits
	anim_ret

BattleAnim_MeanLook:
	anim_1gfx BATTLE_ANIM_GFX_PSYCHIC
	anim_obp0 $e0
	anim_sound 0, 1, SFX_MEAN_LOOK
	anim_obj BATTLE_ANIM_OBJ_MEAN_LOOK, 148, 32, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_MEAN_LOOK, 116, 64, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_MEAN_LOOK, 148, 64, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_MEAN_LOOK, 116, 32, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_MEAN_LOOK, 132, 48, $0
	anim_wait 128
	anim_ret

BattleAnim_Attract:
	anim_1gfx BATTLE_ANIM_GFX_OBJECTS
.loop
	anim_sound 0, 0, SFX_ATTRACT
	anim_obj BATTLE_ANIM_OBJ_ATTRACT, 44, 80, $2
	anim_wait 8
	anim_loop 5, .loop
	anim_wait 192
	anim_ret

BattleAnim_SleepTalk:
	anim_1gfx BATTLE_ANIM_GFX_STATUS
.loop
	anim_sound 0, 0, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_ASLEEP, 64, 80, $0
	anim_wait 40
	anim_loop 2, .loop
	anim_wait 32
	anim_ret

BattleAnim_HealBell:
	anim_2gfx BATTLE_ANIM_GFX_MISC, BATTLE_ANIM_GFX_NOISE
	anim_obj BATTLE_ANIM_OBJ_HEAL_BELL, 72, 56, $0
	anim_wait 32
.loop
	anim_sound 0, 0, SFX_HEAL_BELL
	anim_obj BATTLE_ANIM_OBJ_HEAL_BELL_NOTE, 72, 52, $0
	anim_wait 8
	anim_sound 0, 0, SFX_HEAL_BELL
	anim_obj BATTLE_ANIM_OBJ_HEAL_BELL_NOTE, 72, 52, $1
	anim_wait 8
	anim_sound 0, 0, SFX_HEAL_BELL
	anim_obj BATTLE_ANIM_OBJ_HEAL_BELL_NOTE, 72, 52, $2
	anim_wait 8
	anim_sound 0, 0, SFX_HEAL_BELL
	anim_obj BATTLE_ANIM_OBJ_HEAL_BELL_NOTE, 72, 52, $0
	anim_wait 8
	anim_sound 0, 0, SFX_HEAL_BELL
	anim_obj BATTLE_ANIM_OBJ_HEAL_BELL_NOTE, 72, 52, $2
	anim_wait 8
	anim_loop 4, .loop
	anim_wait 64
	anim_ret

BattleAnim_Return:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_BOUNCE_DOWN, $0, BG_EFFECT_USER, $0
	anim_sound 0, 0, SFX_RETURN
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_BOUNCE_DOWN
	anim_wait 32
	anim_bgeffect BATTLE_BG_EFFECT_BODY_SLAM, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG, 136, 40, $0
	anim_wait 8
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Present:
	anim_2gfx BATTLE_ANIM_GFX_STATUS, BATTLE_ANIM_GFX_BUBBLE
	anim_sound 0, 1, SFX_PRESENT
	anim_obj BATTLE_ANIM_OBJ_PRESENT, 64, 88, $6c
	anim_wait 56
	anim_obj BATTLE_ANIM_OBJ_AMNESIA, 104, 48, $0
	anim_wait 48
	anim_incobj 2
	anim_if_param_equal $3, .heal
	anim_incobj 1
	anim_wait 1
	anim_1gfx BATTLE_ANIM_GFX_EXPLOSION
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $12
.loop
	anim_call BattleAnimSub_Explosion2
	anim_wait 16
	anim_jumpuntil .loop
	anim_ret

.heal
	anim_sound 0, 1, SFX_METRONOME
.loop2
	anim_obj BATTLE_ANIM_OBJ_RECOVER, 132, 48, $24
	anim_wait 8
	anim_loop 8, .loop2
	anim_wait 128
	anim_ret

BattleAnim_Frustration:
	anim_1gfx BATTLE_ANIM_GFX_MISC
	anim_sound 0, 0, SFX_KINESIS_2
	anim_obj BATTLE_ANIM_OBJ_ANGER, 72, 80, $0
	anim_wait 40
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_WOBBLE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 8
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 48, $0
	anim_wait 8
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 152, 48, $0
	anim_wait 8
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 48, $0
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_WOBBLE_MON
	anim_wait 1
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_Safeguard:
	anim_1gfx BATTLE_ANIM_GFX_MISC
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_objparams BATTLE_ANIM_OBJ_SAFEGUARD, 80, 80, 5, $0, $d, $1a, $27, $34
	anim_sound 0, 0, SFX_PROTECT
	anim_wait 96
	anim_ret

BattleAnim_PainSplit:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_OBJECTS
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_BODY_SLAM, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_sound 0, 1, SFX_TACKLE
	anim_obj BATTLE_ANIM_OBJ_HIT, 112, 48, $0
	anim_obj BATTLE_ANIM_OBJ_HIT, 76, 96, $0
	anim_wait 8
	anim_call BattleAnim_ShowMon_0
	anim_wait 1
	anim_ret

BattleAnim_SacredFire:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_firepal BATTLE_ANIM_FIRE_BLUE_PAL_LOAD
.loop1
	anim_sound 0, 0, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_SACRED_FIRE, 48, 104, $0
	anim_wait 8
	anim_loop 8, .loop1
	anim_wait 80
	anim_objparams BATTLE_ANIM_OBJ_SACRED_FIRE_HIT_DELAYED, 136, 48, 2, $24, $25
	anim_wait 16
	anim_objparams BATTLE_ANIM_OBJ_SACRED_FIRE_HIT_DELAYED, 136, 48, 2, $24, $25
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_TACKLE, $0, BG_EFFECT_USER, $0
	anim_wait 4
.loop2
	anim_sound 0, 1, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_SACRED_FIRE_HIT, 136, 48, $1
	anim_wait 16
	anim_loop 2, .loop2
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 4
	anim_incobj 13
	anim_wait 8
	anim_firepal BATTLE_ANIM_FIRE_BLUE_PAL_RESTORE
	anim_ret

BattleAnim_Magnitude:
	anim_1gfx BATTLE_ANIM_GFX_ROCKS
.loop
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $e, $4, $0
	anim_sound 0, 1, SFX_STRENGTH
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 128, 64, $40
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 120, 68, $30
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 152, 68, $30
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 144, 64, $40
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_SMALL_ROCK, 136, 68, $30
	anim_wait 2
	anim_jumpuntil .loop
	anim_wait 96
	anim_ret

BattleAnim_Dynamicpunch:
	anim_2gfx BATTLE_ANIM_GFX_HIT, BATTLE_ANIM_GFX_EXPLOSION
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_PUNCH_SHAKE, 136, 56, $43
	anim_wait 16
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $12
	anim_call BattleAnimSub_Explosion2
	anim_wait 16
	anim_ret

BattleAnim_Megahorn:
	anim_2gfx BATTLE_ANIM_GFX_HORN, BATTLE_ANIM_GFX_HIT
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $40, $2, $0
	anim_wait 48
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $3
	anim_obj BATTLE_ANIM_OBJ_HORN, 72, 80, $1
	anim_sound 0, 1, SFX_HORN_ATTACK
	anim_wait 16
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_Dragonbreath:
	anim_1gfx BATTLE_ANIM_GFX_EMBER
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_LOAD
	anim_call BattleAnimSub_FlamethrowerCore
	anim_dragonpal BATTLE_ANIM_DRAGON_PAL_RESTORE
	anim_ret

BattleAnim_BatonPass:
	anim_1gfx BATTLE_ANIM_GFX_MISC
	anim_obj BATTLE_ANIM_OBJ_BATON_PASS, 44, 104, $20
	anim_sound 0, 0, SFX_BATON_PASS
	anim_call BattleAnimSub_Return
	anim_wait 64
	anim_ret

BattleAnim_Encore:
	anim_1gfx BATTLE_ANIM_GFX_OBJECTS
	anim_objparams BATTLE_ANIM_OBJ_ENCORE_HAND, 64, 80, 2, $90, $10
	anim_sound 0, 0, SFX_ENCORE
	anim_wait 16
	anim_obj BATTLE_ANIM_OBJ_ENCORE_STAR, 64, 72, $2c
	anim_wait 32
	anim_obj BATTLE_ANIM_OBJ_ENCORE_STAR, 64, 72, $34
	anim_wait 16
	anim_ret

BattleAnim_Pursuit:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_if_param_equal $1, .pursued
	anim_sound 0, 1, SFX_COMET_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 56, $0
	anim_wait 16
	anim_ret

.pursued:
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 4
	anim_call BattleAnim_UserObj_1Row
	anim_obj BATTLE_ANIM_OBJ_BETA_PURSUIT, 132, 64, $0
	anim_wait 64
	anim_obj BATTLE_ANIM_OBJ_BETA_PURSUIT, 132, 64, $1
	anim_sound 0, 1, SFX_BALL_POOF
	anim_bgeffect BATTLE_BG_EFFECT_ENTER_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 64
	anim_incobj 3
	anim_wait 16
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 120, 56, $0
	anim_bgeffect BATTLE_BG_EFFECT_BETA_PURSUIT, $0, BG_EFFECT_TARGET, $0
	anim_wait 16
	anim_call BattleAnim_ShowMon_1
	anim_wait 1
	anim_ret

BattleAnim_RapidSpin:
	anim_2gfx BATTLE_ANIM_GFX_WIND, BATTLE_ANIM_GFX_HIT
	anim_obp0 $e4
.loop
	anim_sound 0, 0, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_RAPID_SPIN, 44, 112, $0
	anim_wait 2
	anim_loop 5, .loop
	anim_wait 24
	anim_call BattleAnim_TargetObj_2Row
	anim_bgeffect BATTLE_BG_EFFECT_BODY_SLAM, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_resetobp0
	anim_sound 0, 1, SFX_MEGA_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT, 136, 40, $0
	anim_wait 8
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 4
	anim_incobj 6
	anim_wait 1
	anim_ret

BattleAnim_SweetScent:
	anim_2gfx BATTLE_ANIM_GFX_FLOWER, BATTLE_ANIM_GFX_MISC
	anim_sound 0, 0, SFX_SWEET_SCENT
	anim_obj BATTLE_ANIM_OBJ_FLOWER, 64, 96, $2
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FLOWER, 64, 80, $2
	anim_wait 96
	anim_obp0 $54
	anim_sound 0, 1, SFX_SWEET_SCENT_2
	anim_objparams BATTLE_ANIM_OBJ_COTTON, 136, 40, 3, $15, $2a, $3f
	anim_wait 128
	anim_ret

BattleAnim_IronTail:
	anim_1gfx BATTLE_ANIM_GFX_REFLECT
	anim_obp0 $0
	anim_sound 0, 0, SFX_RAGE
	anim_call BattleAnim_TargetObj_1Row
	anim_call BattleAnimSub_Metallic
	anim_wait 4
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_resetobp0
	anim_bgeffect BATTLE_BG_EFFECT_WOBBLE_MON, $0, BG_EFFECT_USER, $0
	anim_wait 16
	anim_sound 0, 1, SFX_MEGA_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 48, $0
	anim_wait 16
	anim_incbgeffect BATTLE_BG_EFFECT_WOBBLE_MON
	anim_call BattleAnim_ShowMon_0
	anim_ret

BattleAnim_MetalClaw:
	anim_1gfx BATTLE_ANIM_GFX_REFLECT
	anim_obp0 $0
	anim_sound 0, 0, SFX_RAGE
	anim_call BattleAnim_TargetObj_1Row
	anim_call BattleAnimSub_Metallic
	anim_call BattleAnim_ShowMon_0
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_resetobp0
	anim_call BattleAnimSub_ScratchDownLeft
	anim_wait 32
	anim_ret

BattleAnim_VitalThrow:
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_VITAL_THROW, $0, BG_EFFECT_USER, $0
	anim_wait 16
	anim_sound 0, 0, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_HIT, 64, 96, $0
	anim_wait 8
	anim_sound 0, 0, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_HIT, 56, 88, $0
	anim_wait 8
	anim_sound 0, 0, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_HIT, 68, 104, $0
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_VITAL_THROW
	anim_wait 16
	anim_call BattleAnim_ShowMon_0
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG, 132, 56, $0
	anim_wait 16
	anim_ret

BattleAnim_MorningSun:
	anim_1gfx BATTLE_ANIM_GFX_SHINE
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
	anim_sound 0, 0, SFX_MORNING_SUN
.loop
	anim_obj BATTLE_ANIM_OBJ_MORNING_SUN, 16, 48, $88
	anim_wait 6
	anim_loop 5, .loop
	anim_wait 32
	anim_if_param_equal 0, .zero
	anim_call BattleAnimSub_Glimmer
	anim_ret

.zero
	anim_call BattleAnimSub_Glimmer2
	anim_ret

BattleAnim_Synthesis:
	anim_1gfx BATTLE_ANIM_GFX_SHINE
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING, $0, BG_EFFECT_USER, $40
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
	anim_sound 0, 0, SFX_OUTRAGE
	anim_wait 72
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_if_param_equal $1, .one
	anim_call BattleAnimSub_Glimmer
	anim_ret

.one
	anim_call BattleAnimSub_Glimmer2
	anim_ret

BattleAnim_Crunch:
	anim_2gfx BATTLE_ANIM_GFX_SHARP_TEETH, BATTLE_ANIM_GFX_ROCKS
	anim_sound 0, 1, SFX_BITE
	anim_obj BATTLE_ANIM_OBJ_SHARP_TEETH_UPPER, 136, 48, $0
	anim_obj BATTLE_ANIM_OBJ_SHARP_TEETH_LOWER, 136, 66, $1
	anim_wait 7
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $3
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $20, $2, $0
	anim_sound 0, 1, SFX_SPARK
	anim_objparams BATTLE_ANIM_OBJ_CRUNCH_ROCK, 136, 56, 4, $0, $1, $2, $3
	anim_wait 4
	anim_sound 0, 1, SFX_SPARK
	anim_objparams BATTLE_ANIM_OBJ_CRUNCH_ROCK, 136, 56, 4, $4, $5, $6, $7
	anim_wait 24
	anim_ret

BattleAnim_Moonlight:
	anim_1gfx BATTLE_ANIM_GFX_SHINE
	anim_bgp $1b
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $0, $0
	anim_objlist BATTLE_ANIM_OBJ_MOONLIGHT, 5, 0, 40, $0, 16, 56, $0, 32, 72, $0, 48, 88, $0, 64, 104, $0
	anim_wait 1
	anim_sound 0, 0, SFX_MOONLIGHT
	anim_wait 63
	anim_if_param_equal $3, .three
	anim_call BattleAnimSub_Glimmer
	anim_ret

.three
	anim_call BattleAnimSub_Glimmer2
	anim_ret

BattleAnim_HiddenPower:
	anim_1gfx BATTLE_ANIM_GFX_CHARGE
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING, $0, BG_EFFECT_USER, $20
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MID_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_objparams BATTLE_ANIM_OBJ_HIDDEN_POWER, 44, 88, 8, $0, $8, $10, $18, $20, $28, $30, $38
.loop
	anim_sound 0, 0, SFX_SWORDS_DANCE
	anim_wait 8
	anim_loop 12, .loop
	anim_incbgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_wait 1
	anim_incobjrange 2, 8
	anim_wait 16
	anim_1gfx BATTLE_ANIM_GFX_HIT
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 32
	anim_ret

BattleAnim_CrossChop:
	anim_1gfx BATTLE_ANIM_GFX_CUT
	anim_sound 0, 1, SFX_CUT
	anim_obj BATTLE_ANIM_OBJ_CROSS_CHOP1, 152, 40, $0
	anim_obj BATTLE_ANIM_OBJ_CROSS_CHOP2, 120, 72, $0
	anim_wait 8
	anim_bgeffect BATTLE_BG_EFFECT_SHAKE_SCREEN_X, $58, $2, $0
	anim_wait 92
	anim_sound 0, 1, SFX_VICEGRIP
	anim_bgeffect BATTLE_BG_EFFECT_FLASH_INVERTED, $0, $8, $10
	anim_wait 16
	anim_ret

BattleAnim_Twister:
	anim_2gfx BATTLE_ANIM_GFX_WIND, BATTLE_ANIM_GFX_HIT
.loop1
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_obj BATTLE_ANIM_OBJ_GUST, 64, 112, $0
	anim_wait 6
	anim_loop 9, .loop1
.loop2
	anim_sound 0, 0, SFX_RAZOR_WIND
	anim_wait 8
	anim_loop 8, .loop2
	anim_incobjrange 1, 9
	anim_wait 64
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 64, $18
.loop3
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_wait 8
	anim_loop 4, .loop3
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 128, 32, $18
.loop4
	anim_sound 0, 1, SFX_RAZOR_WIND
	anim_wait 8
	anim_loop 4, .loop4
	anim_incobjrange 1, 9
	anim_wait 32
	anim_ret

BattleAnim_RainDance:
	anim_call BattleAnimSub_RainWeather
	anim_wait 128
	anim_ret

BattleAnim_InRain:
	anim_call BattleAnimSub_RainWeather
	anim_wait 48
	anim_ret

BattleAnimSub_RainWeather:
	anim_1gfx BATTLE_ANIM_GFX_WATER
	anim_bgp $f8
	anim_obp0 $7c
	anim_sound 0, 1, SFX_RAIN_DANCE
	anim_obj BATTLE_ANIM_OBJ_RAIN, 88, 0, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_RAIN, 88, 0, $1
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_RAIN, 88, 0, $2
	anim_ret

BattleAnim_SunnyDay:
	anim_call BattleAnimSub_SunWeather
	anim_wait 128
	anim_ret

BattleAnim_InSun:
	anim_call BattleAnimSub_SunWeather
	anim_wait 48
	anim_ret

BattleAnimSub_SunWeather:
	anim_1gfx BATTLE_ANIM_GFX_WATER
	anim_bgp $90
	anim_sound 0, 1, SFX_MORNING_SUN
	anim_obj BATTLE_ANIM_OBJ_RAIN, 88, 0, $2
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_RAIN, 88, 0, $2
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_RAIN, 88, 0, $2
	anim_ret

BattleAnimSub_HailWeather:
	anim_1gfx BATTLE_ANIM_GFX_ICE
	anim_bgeffect BATTLE_BG_EFFECT_WHITE_HUES, $0, $8, $0
	anim_obj BATTLE_ANIM_OBJ_HAIL, 88, 0, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HAIL, 72, 0, $1
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HAIL, 56, 0, $2
	anim_ret

BattleAnim_MirrorCoat:
	anim_2gfx BATTLE_ANIM_GFX_REFLECT, BATTLE_ANIM_GFX_SPEED
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
.loop
	anim_sound 0, 0, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_SCREEN, 72, 80, $0
	anim_obj BATTLE_ANIM_OBJ_SHOOTING_SPARKLE, 64, 72, $4
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SHOOTING_SPARKLE, 64, 88, $4
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SHOOTING_SPARKLE, 64, 80, $4
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SHOOTING_SPARKLE, 64, 96, $4
	anim_wait 8
	anim_loop 3, .loop
	anim_wait 32
	anim_ret

BattleAnim_PsychUp:
	anim_1gfx BATTLE_ANIM_GFX_STATUS
	anim_call BattleAnim_TargetObj_1Row
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING, $0, BG_EFFECT_USER, $20
	anim_sound 0, 0, SFX_PSYBEAM
	anim_objparams BATTLE_ANIM_OBJ_PSYCH_UP, 44, 88, 4, $0, $10, $20, $30
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_CYCLE_MON_LIGHT_DARK_REPEATING
	anim_call BattleAnim_ShowMon_0
	anim_wait 16
	anim_ret

BattleAnim_Extremespeed:
	anim_2gfx BATTLE_ANIM_GFX_SPEED, BATTLE_ANIM_GFX_CUT
	anim_bgeffect BATTLE_BG_EFFECT_HIDE_MON, $0, BG_EFFECT_USER, $0
	anim_sound 0, 0, SFX_MENU
	anim_call BattleAnimSub_SpeedLineBurst
	anim_sound 0, 1, SFX_CUT
	anim_obj BATTLE_ANIM_OBJ_CUT_LONG_DOWN_LEFT, 152, 40, $0
	anim_wait 32
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 16
	anim_ret

BattleAnim_Ancientpower:
	anim_2gfx BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 0, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_ANCIENTPOWER, 64, 108, $20
	anim_wait 8
	anim_sound 0, 0, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_ANCIENTPOWER, 75, 102, $20
	anim_wait 8
	anim_sound 0, 0, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_ANCIENTPOWER, 85, 97, $20
	anim_wait 8
	anim_sound 0, 0, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_ANCIENTPOWER, 96, 92, $20
	anim_wait 8
	anim_sound 0, 1, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_ANCIENTPOWER, 106, 87, $20
	anim_wait 8
	anim_sound 0, 1, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_ANCIENTPOWER, 116, 82, $20
	anim_wait 8
	anim_sound 0, 1, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_ANCIENTPOWER, 126, 77, $20
	anim_wait 8
	anim_sound 0, 1, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 6
	anim_ret

BattleAnim_ShadowBall:
	anim_2gfx BATTLE_ANIM_GFX_EGG, BATTLE_ANIM_GFX_SMOKE
	anim_bgp $1b
	anim_sound 6, 2, SFX_SLUDGE_BOMB
	anim_obj BATTLE_ANIM_OBJ_SHADOW_BALL, 64, 92, $2
	anim_wait 32
	anim_obj BATTLE_ANIM_OBJ_BALL_POOF, 132, 56, $10
	anim_wait 24
	anim_ret

BattleAnim_FutureSight:
	anim_1gfx BATTLE_ANIM_GFX_WIND
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_ALTERNATE_HUES, $0, $2, $0
	anim_bgeffect BATTLE_BG_EFFECT_PSYCHIC, $0, $0, $0
	anim_call BattleAnimSub_AgilityWindLines
.loop
	anim_sound 0, 0, SFX_THROW_BALL
	anim_wait 16
	anim_loop 4, .loop
	anim_incbgeffect BATTLE_BG_EFFECT_PSYCHIC
	anim_ret

BattleAnim_RockSmash:
	anim_2gfx BATTLE_ANIM_GFX_ROCKS, BATTLE_ANIM_GFX_HIT
	anim_sound 0, 1, SFX_SPARK
	anim_obj BATTLE_ANIM_OBJ_PUNCH_SHAKE, 128, 56, $0
	anim_call BattleAnimSub_RockSmashRocks
	anim_wait 32
	anim_ret

BattleAnim_Whirlpool:
	anim_1gfx BATTLE_ANIM_GFX_WIND
	anim_bgeffect BATTLE_BG_EFFECT_WHIRLPOOL, $0, $0, $0
	anim_sound 0, 1, SFX_SURF
	anim_wait 16
.loop
	anim_obj BATTLE_ANIM_OBJ_GUST, 132, 72, $0
	anim_wait 6
	anim_loop 9, .loop
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_WHIRLPOOL
	anim_wait 1
	anim_ret

BattleAnimSub_Drain:
	anim_objparams BATTLE_ANIM_OBJ_DRAIN, 132, 44, 8, $0, $8, $10, $18, $20, $28, $30, $38
	anim_ret

BattleAnimSub_EyeBeams:
	anim_sound 6, 2, SFX_LEER
	anim_objlist BATTLE_ANIM_OBJ_LEER, 8, 72, 84, $0, 64, 80, $0, 88, 76, $0, 80, 72, $0, 104, 68, $0, 96, 64, $0, 120, 60, $0, 112, 56, $0
	anim_objlist BATTLE_ANIM_OBJ_LEER_TIP, 2, 130, 54, $0, 122, 50, $0
	anim_ret

BattleAnimSub_WarpAway:
	anim_sound 0, 0, SFX_WARP_TO
	anim_objlist BATTLE_ANIM_OBJ_WARP, 7, 44, 108, $0, 44, 100, $0, 44, 92, $0, 44, 84, $0, 44, 76, $0, 44, 68, $0, 44, 60, $0
	anim_ret

BattleAnimSub_Beam:
	anim_sound 0, 0, SFX_HYPER_BEAM
	anim_obj BATTLE_ANIM_OBJ_BEAM, 64, 92, $0
	anim_wait 4
	anim_sound 0, 0, SFX_HYPER_BEAM
	anim_obj BATTLE_ANIM_OBJ_BEAM, 80, 84, $0
	anim_wait 4
	anim_sound 0, 1, SFX_HYPER_BEAM
	anim_obj BATTLE_ANIM_OBJ_BEAM, 96, 76, $0
	anim_wait 4
	anim_sound 0, 1, SFX_HYPER_BEAM
	anim_obj BATTLE_ANIM_OBJ_BEAM, 112, 68, $0
	anim_obj BATTLE_ANIM_OBJ_BEAM_TIP, 126, 62, $0
	anim_ret

BattleAnimSub_Explosion1:
	anim_sound 0, 0, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 24, 64, $0
	anim_wait 5
	anim_sound 0, 0, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 56, 104, $0
	anim_wait 5
	anim_sound 0, 0, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 24, 104, $0
	anim_wait 5
	anim_sound 0, 0, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 56, 64, $0
	anim_wait 5
	anim_sound 0, 0, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 40, 84, $0
	anim_ret

BattleAnimSub_Explosion2:
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 148, 32, $0
	anim_wait 5
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 116, 72, $0
	anim_wait 5
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 148, 72, $0
	anim_wait 5
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 116, 32, $0
	anim_wait 5
	anim_sound 0, 1, SFX_EGG_BOMB
	anim_obj BATTLE_ANIM_OBJ_EXPLOSION1, 132, 52, $0
	anim_ret

BattleAnimSub_Sound:
	anim_objlist BATTLE_ANIM_OBJ_SOUND, 3, 64, 76, $0, 64, 88, $1, 64, 100, $2
	anim_ret

BattleAnimSub_BiteJaws:
	anim_objparams BATTLE_ANIM_OBJ_BITE, 136, 56, 2, $98, $18
	anim_ret

BattleAnimSub_MegaPunchHits:
.loop
	anim_sound 0, 1, SFX_MEGA_PUNCH
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_BIG_YFIX, 136, 56, $0
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_PUNCH, 136, 56, $0
	anim_wait 6
	anim_loop 3, .loop
	anim_ret

BattleAnimSub_FocusPunchHits:
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 126, 48, $0
	anim_wait 8
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 146, 58, $0
	anim_wait 8
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 146, 50, $0
	anim_wait 8
	anim_sound 0, 1, SFX_DOUBLE_KICK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 136, 64, $0
	anim_wait 8
	anim_ret

BattleAnimSub_ScratchDownLeft:
	anim_sound 0, 1, SFX_SCRATCH
	anim_objlist BATTLE_ANIM_OBJ_CUT_DOWN_LEFT, 3, 144, 48, $0, 140, 44, $0, 136, 40, $0
	anim_ret

BattleAnimSub_AgilityWindLines:
	anim_objlist BATTLE_ANIM_OBJ_AGILITY, 3, 8, 24, $10, 8, 48, $2, 8, 88, $8
	anim_wait 4
	anim_objlist BATTLE_ANIM_OBJ_AGILITY, 4, 8, 32, $6, 8, 56, $c, 8, 80, $4, 8, 104, $e
	anim_ret

BattleAnimSub_FireSpinOpener:
	anim_sound 6, 2, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FIRE_SPIN, 64, 88, $4
	anim_wait 2
	anim_sound 6, 2, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FIRE_SPIN, 64, 96, $3
	anim_wait 2
	anim_sound 6, 2, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FIRE_SPIN, 64, 88, $3
	anim_wait 2
	anim_sound 6, 2, SFX_EMBER
	anim_obj BATTLE_ANIM_OBJ_FIRE_SPIN, 64, 96, $4
	anim_wait 2
	anim_ret

BattleAnimSub_BlizzardSweep:
	anim_sound 6, 2, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_BLIZZARD, 64, 88, $63
	anim_wait 2
	anim_sound 6, 2, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_BLIZZARD, 64, 80, $64
	anim_wait 2
	anim_sound 6, 2, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_BLIZZARD, 64, 96, $63
	anim_wait 2
	anim_ret

BattleAnimSub_SandstormStart:
	anim_obj BATTLE_ANIM_OBJ_SANDSTORM, 88, 0, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SANDSTORM, 72, 0, $1
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_SANDSTORM, 56, 0, $2
	anim_ret

BattleAnimSub_WingAttackHits:
	anim_sound 0, 1, SFX_WING_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 148, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 116, 56, $0
	anim_wait 6
	anim_sound 0, 1, SFX_WING_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 144, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 120, 56, $0
	anim_wait 6
	anim_sound 0, 1, SFX_WING_ATTACK
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 140, 56, $0
	anim_obj BATTLE_ANIM_OBJ_HIT_YFIX, 124, 56, $0
	anim_wait 16
	anim_ret

BattleAnimSub_RockSmashRocks:
	anim_sound 0, 1, SFX_SPARK
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 128, 64, 2, $28, $5c
	anim_sound 0, 1, SFX_SPARK
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 128, 64, 2, $10, $e8
	anim_sound 0, 1, SFX_SPARK
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 128, 64, 2, $9c, $d0
	anim_wait 6
	anim_sound 0, 1, SFX_SPARK
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 128, 64, 2, $1c, $50
	anim_sound 0, 1, SFX_SPARK
	anim_objparams BATTLE_ANIM_OBJ_ROCK_SMASH, 128, 64, 2, $dc, $90
	anim_ret

BattleAnimSub_Fire:
	anim_sound 0, 1, SFX_EMBER
	anim_objparams BATTLE_ANIM_OBJ_FLAME_WHEEL_HIT, 136, 56, 4, $2, $3, $4, $5
	anim_wait 20
	anim_ret

BattleAnimSub_GhostFlame:
	anim_sound 0, 1, SFX_BURN
	anim_extobjparams BATTLE_ANIM_EXT_OBJ_SHADOW_PUNCH_FLAME, 136, 56, 4, $2, $3, $4, $5
	anim_wait 20
	anim_ret

BattleAnimSub_FireCircle:
	anim_sound 0, 1, SFX_EMBER
.loop
	anim_objparams BATTLE_ANIM_OBJ_BURNED, 136, 56, 2, $18, $98
	anim_wait 4
	anim_loop 4, .loop
	anim_ret

BattleAnimSub_Ice:
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_ICE, 128, 42, $0
	anim_wait 6
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_ICE, 144, 70, $0
	anim_wait 6
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_ICE, 120, 56, $0
	anim_wait 6
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_ICE, 152, 56, $0
	anim_wait 6
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_ICE, 144, 42, $0
	anim_wait 6
	anim_sound 0, 1, SFX_SHINE
	anim_obj BATTLE_ANIM_OBJ_ICE, 128, 70, $0
	anim_ret

BattleAnimSub_ToxicBubbles:
	anim_obj BATTLE_ANIM_OBJ_TOXIC_BUBBLE, 112, 68, $0
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 15
	anim_obj BATTLE_ANIM_OBJ_TOXIC_BUBBLE, 144, 68, $0
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 15
	anim_obj BATTLE_ANIM_OBJ_TOXIC_BUBBLE, 128, 68, $0
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 15
	anim_obj BATTLE_ANIM_OBJ_TOXIC_BUBBLE, 160, 68, $0
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 15
	anim_ret

BattleAnimSub_Metallic:
	anim_sound 0, 0, SFX_SHINE
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK, $0, BG_EFFECT_USER, $40
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HARDEN, 48, 84, $0
	anim_wait 32
	anim_obj BATTLE_ANIM_OBJ_HARDEN, 48, 84, $0
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_BLACK
	anim_ret

BattleAnimSub_PoisonMetallic:
	anim_sound 0, 0, SFX_SHINE
	anim_bgeffect BATTLE_BG_EFFECT_POISON_METALLIC, $0, BG_EFFECT_USER, $0
	anim_wait 8
	anim_obj BATTLE_ANIM_OBJ_HARDEN, 48, 84, $0
	anim_wait 32
	anim_obj BATTLE_ANIM_OBJ_HARDEN, 48, 84, $0
	anim_wait 64
	anim_incbgeffect BATTLE_BG_EFFECT_POISON_METALLIC
	anim_ret

BattleAnimSub_SandOrMud:
.loop
	anim_sound 6, 2, SFX_MENU
	anim_obj BATTLE_ANIM_OBJ_SAND, 64, 92, $4
	anim_wait 4
	anim_loop 8, .loop
	anim_wait 32
	anim_ret

BattleAnimSub_Glimmer:
	anim_sound 0, 0, SFX_METRONOME
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 44, 64, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 24, 96, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 56, 104, $0
	anim_wait 21
	anim_ret

BattleAnimSub_Glimmer2:
	anim_sound 0, 0, SFX_METRONOME
.loop
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 24, 64, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 56, 104, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 24, 104, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 56, 64, $0
	anim_wait 5
	anim_obj BATTLE_ANIM_OBJ_GLIMMER, 40, 84, $0
	anim_wait 5
	anim_loop 2, .loop
	anim_wait 16
	anim_ret

BattleAnimSub_FocusEnergy:
	anim_1gfx BATTLE_ANIM_GFX_SPEED
	anim_battlergfx_2row
	anim_bgeffect BATTLE_BG_EFFECT_BATTLEROBJ_1ROW, $0, BG_EFFECT_TARGET, $0
	anim_wait 6
	anim_bgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT, $0, BG_EFFECT_USER, $40
	anim_bgeffect BATTLE_BG_EFFECT_CYCLE_OBPALS_GRAY_AND_YELLOW, $0, $2, $0
.loop
	anim_call BattleAnimSub_FocusEnergyBurst
	anim_loop 3, .loop
	anim_wait 8
	anim_incbgeffect BATTLE_BG_EFFECT_FADE_MON_TO_LIGHT
	anim_wait 1
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 5
	anim_incobj 1
	anim_wait 1
	anim_ret

BattleAnimSub_FocusEnergyBurst:
	anim_sound 0, 0, SFX_SWORDS_DANCE
	anim_obj BATTLE_ANIM_OBJ_FOCUS, 44, 108, $6
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FOCUS, 36, 108, $6
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FOCUS, 52, 108, $8
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FOCUS, 28, 108, $8
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FOCUS, 60, 108, $6
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FOCUS, 20, 108, $8
	anim_wait 2
	anim_obj BATTLE_ANIM_OBJ_FOCUS, 68, 108, $8
	anim_wait 2
	anim_ret

BattleAnimSub_SpeedLineBurst:
	anim_objlist BATTLE_ANIM_OBJ_SPEED_LINE, 6, 24, 88, $2, 32, 88, $1, 40, 88, $0, 48, 88, $80, 56, 88, $81, 64, 88, $82
	anim_wait 12
	anim_ret

BattleAnimSub_PoisonBubblesEffect:
	anim_obj BATTLE_ANIM_OBJ_POISON_BUBBLE, 146, 66, $80
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_POISON_BUBBLE, 156, 36, $80
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_POISON_BUBBLE, 116, 71, $80
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_POISON_BUBBLE, 136, 56, $80
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_POISON_BUBBLE, 116, 36, $80
	anim_sound 0, 1, SFX_TOXIC
	anim_wait 6
	anim_obj BATTLE_ANIM_OBJ_POISON_BUBBLE, 152, 48, $80
	anim_sound 0, 1, SFX_TOXIC
	anim_ret

BattleAnim_TargetObj_1Row:
	anim_battlergfx_2row
	anim_bgeffect BATTLE_BG_EFFECT_BATTLEROBJ_1ROW, $0, BG_EFFECT_TARGET, $0
	anim_wait 6
	anim_ret

BattleAnim_TargetObj_2Row:
	anim_battlergfx_1row
	anim_bgeffect BATTLE_BG_EFFECT_BATTLEROBJ_2ROW, $0, BG_EFFECT_TARGET, $0
	anim_wait 6
	anim_ret

BattleAnim_ShowMon_0:
	anim_wait 1
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_TARGET, $0
	anim_wait 5
	anim_incobj 1
	anim_wait 1
	anim_ret

BattleAnim_UserObj_1Row:
	anim_battlergfx_2row
	anim_bgeffect BATTLE_BG_EFFECT_BATTLEROBJ_1ROW, $0, BG_EFFECT_USER, $0
	anim_wait 6
	anim_ret

BattleAnim_UserObj_2Row:
	anim_battlergfx_1row
	anim_bgeffect BATTLE_BG_EFFECT_BATTLEROBJ_2ROW, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_ret

BattleAnim_ShowMon_1:
	anim_wait 1
	anim_bgeffect BATTLE_BG_EFFECT_SHOW_MON, $0, BG_EFFECT_USER, $0
	anim_wait 4
	anim_incobj 1
	anim_wait 1
	anim_ret
