BattleAnim_UpdateFunctions_All:
	xor a
	ld [wBattleAnimUpdatedCount], a
	ld hl, wActiveAnimObjects
	ld e, NUM_BATTLE_ANIM_STRUCTS
.loop
	ld a, [hl]
	and a
	jr z, .next
	ld c, l
	ld b, h
	push hl
	push de
	call DoBattleAnimFrame
	pop de
	pop hl
	call BattleAnim_AppendUpdatedObject

.next
	ld bc, BATTLEANIMSTRUCT_LENGTH
	add hl, bc
	dec e
	jr nz, .loop
	ret

BattleAnim_AppendUpdatedObject:
; Input: hl = original anim object struct pointer.
; Preserves hl and de for the update loop.
	push hl
	push de
	ld a, [wBattleAnimUpdatedCount]
	ld e, a
	inc a
	ld [wBattleAnimUpdatedCount], a
	ld d, 0
	ld hl, wBattleAnimUpdatedObjects
	add hl, de
	add hl, de
	pop de
	pop bc
	ld [hl], c
	inc hl
	ld [hl], b
	ld h, b
	ld l, c
	ret

; Input: D = frameset namespace (0 = regular, 1 = extended), E = frameset index
ReinitBattleAnimFrameset:
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld [hl], e
	inc hl
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], 0
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], -1
	ret

DoBattleAnimFrame:
	ld hl, BATTLEANIMSTRUCT_FUNCTION
	add hl, bc
	ld e, [hl]
	ld d, 0
	ld hl, .Jumptable
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jp hl

.Jumptable:
; entries correspond to BATTLE_ANIM_FUNC_* constants
	table_width 2
	dw BattleAnimFunc_Null
	dw BattleAnimFunc_MoveFromUserToTarget
	dw BattleAnimFunc_MoveFromUserToTargetAndDisappear
	dw BattleAnimFunc_MoveInCircle
	dw BattleAnimFunc_MoveWaveToTarget
	dw BattleAnimFunc_ThrowFromUserToTarget
	dw BattleAnimFunc_ThrowFromUserToTargetAndDisappear
	dw BattleAnimFunc_Drop
	dw BattleAnimFunc_MoveFromUserToTargetSpinAround
	dw BattleAnimFunc_Shake
	dw BattleAnimFunc_FireBlast
	dw BattleAnimFunc_RazorLeaf
	dw BattleAnimFunc_Bubble
	dw BattleAnimFunc_Surf
	dw BattleAnimFunc_Sing
	dw BattleAnimFunc_WaterGun
	dw BattleAnimFunc_Ember
	dw BattleAnimFunc_Powder
	dw BattleAnimFunc_PokeBall
	dw BattleAnimFunc_PokeBallBlocked
	dw BattleAnimFunc_Recover
	dw BattleAnimFunc_ThunderWave
	dw BattleAnimFunc_Clamp_Encore
	dw BattleAnimFunc_Bite
	dw BattleAnimFunc_SolarBeam
	dw BattleAnimFunc_Gust
	dw BattleAnimFunc_RazorWind
	dw BattleAnimFunc_Kick
	dw BattleAnimFunc_Absorb
	dw BattleAnimFunc_Egg
	dw BattleAnimFunc_MoveUp
	dw BattleAnimFunc_Wrap
	dw BattleAnimFunc_LeechSeed
	dw BattleAnimFunc_Sound
	dw BattleAnimFunc_ConfuseRay
	dw BattleAnimFunc_Dizzy
	dw BattleAnimFunc_Amnesia
	dw BattleAnimFunc_FloatUp
	dw BattleAnimFunc_Dig
	dw BattleAnimFunc_String
	dw BattleAnimFunc_Paralyzed
	dw BattleAnimFunc_SpiralDescent
	dw BattleAnimFunc_PoisonGas
	dw BattleAnimFunc_Horn
	dw BattleAnimFunc_Needle
	dw BattleAnimFunc_PetalDance
	dw BattleAnimFunc_ThiefPayday
	dw BattleAnimFunc_AbsorbCircle
	dw BattleAnimFunc_Bonemerang
	dw BattleAnimFunc_Shiny
	dw BattleAnimFunc_SkyAttack
	dw BattleAnimFunc_GrowthSwordsDance
	dw BattleAnimFunc_SmokeFlameWheel
	dw BattleAnimFunc_PresentSmokescreen
	dw BattleAnimFunc_StrengthSeismicToss
	dw BattleAnimFunc_SpeedLine
	dw BattleAnimFunc_MetronomeHand
	dw BattleAnimFunc_MetronomeSparkleSketch
	dw BattleAnimFunc_Agility
	dw BattleAnimFunc_SacredFire
	dw BattleAnimFunc_SafeguardProtect
	dw BattleAnimFunc_LockOnMindReader
	dw BattleAnimFunc_Spikes
	dw BattleAnimFunc_HealBellNotes
	dw BattleAnimFunc_BatonPass
	dw BattleAnimFunc_Conversion
	dw BattleAnimFunc_EncoreBellyDrum
	dw BattleAnimFunc_SwaggerMorningSun
	dw BattleAnimFunc_HiddenPower
	dw BattleAnimFunc_Curse
	dw BattleAnimFunc_PerishSong
	dw BattleAnimFunc_RapidSpin
	dw BattleAnimFunc_BetaPursuit
	dw BattleAnimFunc_RainSandstorm
	dw BattleAnimFunc_PsychUp
	dw BattleAnimFunc_AncientPower
	dw BattleAnimFunc_RockSmash
	dw BattleAnimFunc_Cotton
	dw BattleAnimFunc_Flamethrower
	dw BattleAnimFunc_OutrageFlame
	dw BattleAnimFunc_PoisonPowder
	dw BattleAnimFunc_BulletSeed
	dw BattleAnimFunc_ExtNull
	dw BattleAnimFunc_WishStar
	dw BattleAnimFunc_SeismicTossLight
	dw BattleAnimFunc_MudShot
	dw BattleAnimFunc_AromatherapyFlower
	dw BattleAnimFunc_OverheatFlame
	dw BattleAnimFunc_Thunder
	dw BattleAnimFunc_WaterfallBubble
	dw BattleAnimFunc_FireBlastModern
	dw BattleAnimFunc_EmberGen3
	dw BattleAnimFunc_FlameWheelHit
	dw BattleAnimFunc_SacredFireHit
	dw BattleAnimFunc_LavaPlumeEruption
	dw BattleAnimFunc_DragonClawFlame
	dw BattleAnimFunc_ShadowClawFlame
	dw BattleAnimFunc_PoisonBubble
	dw BattleAnimFunc_SludgeBomb
	dw BattleAnimFunc_AcidBubble
	dw BattleAnimFunc_AcidDroplet
	dw BattleAnimFunc_CrunchJaw
	dw BattleAnimFunc_CrunchRock
	dw BattleAnimFunc_WaterPulseDriftBubble
	dw BattleAnimFunc_ThunderStrikeController
	dw BattleAnimFunc_SilverWind
	dw BattleAnimFunc_IceChunk
	dw BattleAnimFunc_StoneEdgeRock
	dw BattleAnimFunc_ShockWaveOrb
	dw BattleAnimFunc_BlockX
	dw BattleAnimFunc_ForcePalm
	dw BattleAnimFunc_IngrainRoot
	dw BattleAnimFunc_IngrainOrb
	dw BattleAnimFunc_TauntPlaced
	dw BattleAnimFunc_HexMeanLook
	dw BattleAnimFunc_HexGhostFlame
	dw BattleAnimFunc_WillOWispBubble
	dw BattleAnimFunc_WillOWispPlusFlame
	dw BattleAnimFunc_DragonDanceOrb
	dw BattleAnimFunc_FakeOutHand
	dw BattleAnimFunc_YawnCloud
	dw BattleAnimFunc_YawnBubble
	dw BattleAnimFunc_SandTombFleck
	dw BattleAnimFunc_AromatherapyPetal
	dw BattleAnimFunc_AuroraBeamRing
	dw BattleAnimFunc_VoltTackleBolt
	dw BattleAnimFunc_BlizzardWindSheet
	dw BattleAnimFunc_PetalDancePetal
	dw BattleAnimFunc_PetalDanceTargetPetal
	dw BattleAnimFunc_ShadowBall
	dw BattleAnimFunc_ChargeCenter
	dw BattleAnimFunc_PetalDanceController
	dw BattleAnimFunc_ThunderboltAftereffectController
	dw BattleAnimFunc_MeteorMashController
	dw BattleAnimFunc_DrainLifeBite
	dw BattleAnimFunc_VampirismBite
	dw BattleAnimFunc_LeafBlade
	dw BattleAnimFunc_LeafBladeChip
	dw BattleAnimFunc_SuperpowerRockChip
	dw BattleAnimFunc_DisarmingVoiceNote
	dw BattleAnimFunc_CausticBubble
	dw BattleAnimFunc_SolarBeamVerticalSegment
	dw BattleAnimFunc_IronDefenseGlimmer
	dw BattleAnimFunc_AerialCrash
	dw BattleAnimFunc_MeteorDiveGlobe
	dw BattleAnimFunc_AeroblastWave
	dw BattleAnimFunc_DiveBombWind
	dw BattleAnimFunc_BrickBreakShard
	dw BattleAnimFunc_PokeBallBG
	dw BattleAnimFunc_CatchSparkle
	assert_table_length NUM_BATTLE_ANIM_FUNCS

BattleAnimFunc_Null:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
.one
	call BattleAnimExt_Deinit
.zero
	ret

BattleAnimFunc_ThrowFromUserToTargetAndDisappear:
	call BattleAnimFunc_ThrowFromUserToTarget
	ret c
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_ThrowFromUserToTarget:
	; If x coord at $88 or beyond, abort.
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $88
	ret nc
	; Move right 2 pixels
	add $2
	ld [hl], a
	; Move down 1 pixel
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	; Decrease var1 and hold onto its previous value (argument of the sine function)
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec [hl]
	; Get param (amplitude of the sine function)
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	call BattleAnim_Sine
	; Store the sine result in the Y offset
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	; Carry flag denotes success
	scf
	ret

BattleAnimFunc_MoveWaveToTarget:
; Wave motion from one mon to another. Obj is cleared when it reaches x coord $88. Examples: Shadow Ball, Dragon Rage
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $88
	jr c, .move
	call BattleAnimExt_Deinit
	ret

.move
	add $2
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	inc [hl]
	inc [hl]
	inc [hl]
	ld d, $10
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	sra a
	sra a
	sra a
	sra a
	ld [hl], a
	ret

BattleAnimFunc_MoveInCircle:
; Slow circular motion. Examples: Thundershock, Flamethrower
; Obj Param: Distance from center (masked with $7F). Bit 7 causes object to start on other side of the circle
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	ld a, $0
	jr z, .got_starting_position
	ld a, $20
.got_starting_position
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], 20
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7f
	ld [hl], a
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	dec [hl]
	ret nz
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_Flamethrower:
; Original no-delete circular motion. Script clears these objects explicitly.
; Obj Param: Distance from center (masked with $7F). Bit 7 starts on the opposite side.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	ld a, $0
	jr z, .got_starting_position
	ld a, $20
.got_starting_position
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7f
	ld [hl], a
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

BattleAnimFunc_OutrageFlame:
; Obj Param: $0-$7 = forward-only flame vector.
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 30
	jr nc, .done
	inc [hl]

	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	add a
	ld e, a
	ld d, 0

	ld hl, .PlayerVectors
	ldh a, [hBattleTurn]
	and a
	jr z, .got_vectors
	ld hl, .EnemyVectors

.got_vectors
	add hl, de
	ld e, [hl]
	inc hl
	ld d, [hl]

	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a

	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a
	ldh a, [hBattleTurn]
	and a
	ret z
	ld a, [hl]
	cp $28
	ret nc
	; Opponent-side flames render downward as raw Y decreases.
	; Delete before they enter the text box.
	jr .done

.done
	call BattleAnimExt_Deinit
	ret

.PlayerVectors:
; player-side rendered paths: broader upward wild burst
	db  2, -4 ; $0 steep up-forward
	db  3, -3 ; $1 up-forward
	db  4, -1 ; $2 more shallow/targetward
	db  4,  0 ; $3 straight right
	db  3, -2 ; $4 lower wave carry
	db  3, -3 ; $5 mid upward
	db  1, -4 ; $6 near-vertical
	db  3,  0 ; $7 lower forward lane

.EnemyVectors:
; opponent-side tuned to stay on-screen with valid travel toward the player.
	db  4, -2 ; $0 down-left
	db  4, -2 ; $1 down-left
	db  5, -1 ; $2 shallow down-left
	db  4,  0 ; $3 straight left
	db  3, -1 ; $4 slower shallow down-left
	db  3, -3 ; $5 steeper/slower down-left
	db  3, -3 ; $6 steeper down-left
	db  4,  0 ; $7 straight left

BattleAnimFunc_MoveFromUserToTarget:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
.one
	call BattleAnimExt_Deinit
	ret

.zero
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $84
	ret nc
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	call BattleAnim_StepToTarget
	ret

BattleAnimFunc_MoveFromUserToTargetAndDisappear:
; Same as BattleAnimFunc_01 but objs are cleared when they reach x coord $84
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $84
	jr nc, .done
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	call BattleAnim_StepToTarget
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_PokeBallBG:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw BattleAnimFunc_PokeBall.one
	dw BattleAnimFunc_PokeBall.two
	dw BattleAnimFunc_PokeBall.three
	dw BattleAnimFunc_PokeBall.four
	dw BattleAnimFunc_PokeBall.five
	dw BattleAnimFunc_PokeBall.six
	dw BattleAnimFunc_PokeBall.seven
	dw BattleAnimFunc_PokeBall.eight
	dw BattleAnimFunc_PokeBall.nine
	dw BattleAnimFunc_PokeBall.ten
	dw BattleAnimFunc_PokeBall.eleven

.zero
	call GetBallAnimBGPal
	call BattleAnim_IncAnonJumptableIndex
	ret

BattleAnimFunc_PokeBall:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
	dw .four
	dw .five
	dw .six
	dw .seven
	dw .eight
	dw .nine
	dw .ten
	dw .eleven
.zero ; init
	call GetBallAnimPal
	call BattleAnim_IncAnonJumptableIndex
	ret

.one
	call BattleAnimFunc_ThrowFromUserToTarget
	ret c
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	add [hl]
	ld [hl], a
	ld de, BATTLE_ANIM_FRAMESET_POKE_BALL_3
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ret

.three
	call BattleAnim_IncAnonJumptableIndex
	ld de, BATTLE_ANIM_FRAMESET_POKE_BALL_1
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $0
	inc hl
	ld [hl], $10
.four
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hli]
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec a
	ld [hl], a
	and $1f
	ret nz
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	sub $4
	ld [hl], a
	ret nz
	ld de, BATTLE_ANIM_FRAMESET_POKE_BALL_4
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ret

.six
	ld de, BATTLE_ANIM_FRAMESET_POKE_BALL_5
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	dec [hl]
.two
.five
.nine
	ret

.seven
	call GetBallAnimPal
	ld de, BATTLE_ANIM_FRAMESET_POKE_BALL_2
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], $20
.eight
.ten
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hli]
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec a
	ld [hl], a
	and $1f
	jr z, .eleven
	and $f
	ret nz
	call BattleAnim_IncAnonJumptableIndex
	ret

.eleven
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_PokeBallBlocked:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
.zero
	call GetBallAnimPal
	call BattleAnim_IncAnonJumptableIndex
	ret

.one
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $70
	jr nc, .next
	call BattleAnimFunc_ThrowFromUserToTarget
	ret

.next
	call BattleAnim_IncAnonJumptableIndex
.two
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	cp $80
	jr nc, .done
	add $4
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	dec [hl]
	dec [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

GetBallAnimPal:
	ld hl, BATTLEANIMSTRUCT_PALETTE
	add hl, bc
	ld [hl], PAL_BATTLE_OB_RED
	ret

GetBallAnimBGPal:
	ld hl, BATTLEANIMSTRUCT_PALETTE
	add hl, bc
	ld [hl], PAL_BATTLE_OB_GREEN
	ret

BattleAnimFunc_CatchSparkle:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $10
	jr nc, .done
	inc [hl]
	inc [hl]
	ld d, a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_Ember:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
	dw .four
.zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	swap a
	and $f
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], a
	ret

.one
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $88
	ret nc
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	call BattleAnim_StepToTarget
	ret

.two
	call BattleAnimExt_Deinit
	ret

.three
	call BattleAnim_IncAnonJumptableIndex
	ld de, BATTLE_ANIM_FRAMESET_FLAMETHROWER
	call ReinitBattleAnimFrameset
.four
	ret

BattleAnimFunc_Drop:
; Drops obj. The Obj Param dictates how fast it is (lower value is faster) and how long it stays bouncing (lower value is longer). Example: Rock Slide
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $30
	inc hl
	ld [hl], $48
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hli]
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $3f
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $20
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	sub [hl]
	jr z, .done
	jr c, .done
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_MoveFromUserToTargetSpinAround:
; Object moves from user to target target and spins around it once. Example: Fire Spin, Swift
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
.zero
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $80
	jr nc, .next
	call .SetCoords
	ret

.next
	call BattleAnim_IncAnonJumptableIndex
.one
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $0
.two
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $40
	jr nc, .loop_back
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $18
	call BattleAnim_Cosine
	sub $18
	sra a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $18
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	add [hl]
	ld [hl], a
	ret

.loop_back
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	jr z, .finish
	sub $10
	ld d, a
	ld a, [hl]
	and $f
	or d
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	dec [hl]
	ret

.finish
	call BattleAnim_IncAnonJumptableIndex
.three
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $b0
	jr c, .retain
	call BattleAnimExt_Deinit
	ret

.retain
	call .SetCoords
	ret

.SetCoords:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	add [hl]
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld e, a
	srl e
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
.loop
	dec [hl]
	dec e
	jr nz, .loop
	ret

BattleAnimFunc_Shake:
; Object switches position side to side. Obj Param defines how far to move it. Example: Dynamic Punch
; Some objects use this function with a Param of 0
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .done_one
	dec [hl]
	ret

.done_one
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	swap a
	and $f
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	xor $ff
	inc a
	ld [hl], a
	ret

.two
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_FireBlast:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
	dw .four
	dw .five
	dw .six
	dw .seven
	dw .eight
	dw .nine
.zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], a
	cp $7
	jr z, .seven
	ld de, BATTLE_ANIM_FRAMESET_EMBER_1_2_3_4_5
	call ReinitBattleAnimFrameset
	ret

.seven
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $88
	jr nc, .set_up_eight
	add $2
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ret

.set_up_eight
	call BattleAnim_IncAnonJumptableIndex
	ld de, BATTLE_ANIM_FRAMESET_EMBER_1_2_3_4_5
	call ReinitBattleAnimFrameset
.eight
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $10
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

.nine
	call BattleAnimExt_Deinit
	ret

.one
	; Flame that moves upward
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	dec [hl]
	ret

.four
	; Flame that moves down and left
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
.two
	; Flame that moves left
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	dec [hl]
	ret

.five
	; Flame that moves down and right
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
.three
	; Flame that moves right
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	inc [hl]
.six
	ret

; Razor Leaf impact tuning. RAZOR_LEAF_HIT_X_* is the internal XCOORD at which a
; leaf spawns its hit; it is turn-specific because the renderer mirrors X on the
; enemy turn, so one internal value lands on opposite sides of the screen. The
; enemy descent is flattened (vs the player turn's 4) so the mirrored, downward
; impact dash stays above the text box. Set RAZOR_LEAF_ENEMY_STEP_Y to 4 to
; disable the flatten (enemy dash then matches the player turn).
DEF RAZOR_LEAF_HIT_X_PLAYER EQU $7c ; enemy mon box center
DEF RAZOR_LEAF_HIT_X_ENEMY  EQU $84 ; player mon, after the X mirror
DEF RAZOR_LEAF_STEP_X       EQU $8  ; horizontal dash speed (both turns)
DEF RAZOR_LEAF_ENEMY_STEP_Y EQU 2   ; enemy-turn descent per step

BattleAnimFunc_RazorLeaf:
; Object moves at an arc
; Obj Param: Bit 6 defines offset from base frameset BATTLE_ANIM_FRAMESET_RAZOR_LEAF_2
;            Rest defines arc radius
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
	dw .four
	dw .five
	dw .six
	dw .seven
	dw .eight
	dw .nine
.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $40
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $30
	jr nc, .sine_cosine
	call BattleAnim_IncAnonJumptableIndex
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hli], a
	ld [hl], a
	ld de, BATTLE_ANIM_FRAMESET_RAZOR_LEAF_2
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 6, [hl]
	ret z
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], $5
	ret

.sine_cosine
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3f
	ld d, a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	call BattleAnim_ScatterHorizontal
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld h, [hl]
	ld l, a
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	ret

.two
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $20
	jr nz, .sine_cosine_2
	call BattleAnimExt_Deinit
	ret

.sine_cosine_2
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $10
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 6, [hl]
	jr nz, .decrease
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	jr .finish

.decrease
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	dec [hl]
.finish
	ld de, $80
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld h, [hl]
	ld l, a
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	ret

.three
	ld de, BATTLE_ANIM_FRAMESET_RAZOR_LEAF_1
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_OAMFLAGS
	add hl, bc
	res B_OAM_XFLIP, [hl]
.four
.five
.six
.seven
	call BattleAnim_IncAnonJumptableIndex
	ret

.eight
; Flying toward the target. Spawn one hit when we reach it, then keep flying.
	ldh a, [hBattleTurn]
	and a
	ld d, RAZOR_LEAF_HIT_X_PLAYER
	jr z, .got_threshold
	ld d, RAZOR_LEAF_HIT_X_ENEMY
.got_threshold
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp d
	jr c, .eight_step
	call BattleAnimFunc_RazorLeaf_SpawnHit
	call BattleAnim_IncAnonJumptableIndex
.eight_step
	call BattleAnimFunc_RazorLeaf_Step
	ret

.nine
; Already struck; finish flying off-screen without spawning further hits.
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $c0
	ret nc
	call BattleAnimFunc_RazorLeaf_Step
	ret

BattleAnimFunc_RazorLeaf_SpawnHit:
; Spawn a small hit at this leaf's current position. Preserves Razor Leaf's
; tuned enemy-side fix-y; Magical Leaf uses this path too.
	ld a, $78
	jr BattleAnimFunc_SpawnSmallHitAtObject

BattleAnimFunc_BulletSeed_SpawnHit:
; Spawn a small hit at this seed's current position, using the seed's own fix-y
; so enemy-side hits line up with Bullet Seed's mirrored trajectory.
	ld hl, BATTLEANIMSTRUCT_FIX_Y
	add hl, bc
	ld a, [hl]
	jr BattleAnimFunc_SpawnSmallHitAtObject

BattleAnimFunc_SpawnSmallHitAtObject:
; Spawn a small hit at the current object's position, copying X/Y and X/Y
; offsets. Input: a = desired fix-y for the spawned hit. Preserves bc.
	push af
	ld a, BATTLE_ANIM_OBJ_HIT_SMALL
	ld [wBattleObjectTempID], a
	xor a
	ld [wBattleObjectTempNamespace], a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	ld [wBattleObjectTempXCoord], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	ld [wBattleObjectTempYCoord], a
	xor a
	ld [wBattleObjectTempParam], a
	push bc
	callfar QueueBattleAnimation
	jr c, .full
	ld hl, BATTLEANIMSTRUCT_FIX_Y
	add hl, bc
	pop de
	pop af
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld b, d
	ld c, e
	ret
.full
	pop bc
	pop af
	ret

BattleAnimFunc_RazorLeaf_Step:
; Advance the leaf along its impact dash. The player turn uses the standard
; diagonal step; the enemy turn keeps the same horizontal speed but a flatter
; descent (RAZOR_LEAF_ENEMY_STEP_Y) so the mirrored, downward path stays above
; the text box on the lower-left. Preserves bc.
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy
	ld a, RAZOR_LEAF_STEP_X
	call BattleAnim_StepToTarget
	ret
.enemy
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	add RAZOR_LEAF_STEP_X
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub RAZOR_LEAF_ENEMY_STEP_Y
	ld [hl], a
	ret

BattleAnim_ScatterHorizontal:
; Affects horizontal sine movement based on bit 7 of Obj Param
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	bit 7, a
	jr nz, .negative
	cp $20
	jr nc, .plus_256
	cp $18
	jr nc, .plus_384
	ld de, $200
	ret

.plus_384
	ld de, $180
	ret

.plus_256
	ld de, $100
	ret

.negative
	and %00111111
	cp $20
	jr nc, .minus_256
	cp $18
	jr nc, .minus_384
	ld de, -$200
	ret

.minus_384
	ld de, -$180
	ret

.minus_256
	ld de, -$100
	ret

BattleAnimFunc_RockSmash:
; Object moves at an arc
; Obj Param: Bit 7 makes arc flip horizontally
;            Bit 6 defines offset from base frameset FRAMESET_19
;            Rest defines arc radius
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
.zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $40
	rlca
	rlca
	add BATTLE_ANIM_FRAMESET_BIG_ROCK
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $40
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $30
	jr nc, .sine_cosine
	call BattleAnimExt_Deinit
	ret

.sine_cosine
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3f
	ld d, a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	call BattleAnim_ScatterHorizontal
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld h, [hl]
	ld l, a
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	ret

BattleAnimFunc_Bubble:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $c
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .next
	dec [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	call BattleAnim_StepToTarget
	ret

.next
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $0
	ld de, BATTLE_ANIM_FRAMESET_PULSING_BUBBLE
	call ReinitBattleAnimFrameset
.two
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $98
	jr nc, .okay
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld h, [hl]
	ld l, a
	ld de, $60
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], d
.okay
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	cp $20
	ret c
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	ld e, a
	ld d, $ff
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld h, [hl]
	ld l, a
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], d
	ret

BattleAnimFunc_Surf:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
	dw .four
.zero
	call BattleAnim_IncAnonJumptableIndex
	ld a, LOW(rSCY)
	ldh [hLCDCPointer], a
	ld a, $58
	ldh [hLYOverrideStart], a
	ld a, $5e
	ldh [hLYOverrideEnd], a
	ret

.one
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	cp e
	jr nc, .move
	call BattleAnim_IncAnonJumptableIndex
	xor a
	ldh [hLYOverrideStart], a
	ret

.move
	dec a
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $10
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	add [hl]
	sub $10
	ret c
	ldh [hLYOverrideStart], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	inc a
	and $7
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	inc [hl]
.two
	ret

.three
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	cp $70
	jr c, .move_down
	xor a
	ldh [hLCDCPointer], a
	ldh [hLYOverrideStart], a
	ldh [hLYOverrideEnd], a
.four
	call BattleAnimExt_Deinit
	ret

.move_down
	inc a
	inc a
	ld [hl], a
	sub $10
	ret c
	ldh [hLYOverrideStart], a
	ret

BattleAnimFunc_Sing:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_1
	assert BATTLE_ANIM_FRAMESET_MUSIC_NOTE_1 + 1 == BATTLE_ANIM_FRAMESET_MUSIC_NOTE_2 \
		&& BATTLE_ANIM_FRAMESET_MUSIC_NOTE_2 + 1 == BATTLE_ANIM_FRAMESET_MUSIC_NOTE_3
	add [hl]
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset

.one
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $b8
	jr c, .move
	call BattleAnimExt_Deinit
	ret

.move
	ld a, $2
	call BattleAnim_StepToTarget
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec [hl]
	ld d, $8
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleAnimFunc_WaterGun:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three

.zero
	call BattleAnim_IncAnonJumptableIndex
.one
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	cp $30
	jr c, .run_down
	ld a, $2
	call BattleAnim_StepToTarget
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec [hl]
	ld d, $8
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

.run_down
	call BattleAnim_IncAnonJumptableIndex
	ld de, BATTLE_ANIM_FRAMESET_WATER_GUN_2
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], $30
	ld hl, BATTLEANIMSTRUCT_OAMFLAGS
	add hl, bc
	ld a, [hl]
	and 1 << BATTLEANIMSTRUCT_OAMFLAGS_FIX_COORDS_F
	ld [hl], a
.two
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $18
	jr nc, .splash
	inc [hl]
	ret

.splash
	call BattleAnim_IncAnonJumptableIndex
	ld de, BATTLE_ANIM_FRAMESET_WATER_GUN_3
	call ReinitBattleAnimFrameset
.three
	ret

BattleAnimFunc_Powder:
; Obj moves down and disappears at x coord $38
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $38
	jr c, .move
	call BattleAnimExt_Deinit
	ret

.move
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld l, [hl]
	ld h, a
	ld de, $80
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], d
	; Shakes object back and forth 16 pixels
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	xor $10
	ld [hl], a
	ret

BattleAnimFunc_PoisonPowder:
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .active
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	xor a
	ld [hl], a
	ret

.active
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp POISON_POWDER_CONTROLLER_LIFETIME
	ret c
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_BulletSeed:
; Seed travels to the target, then scatters in an Emerald-style impact arc.
; Obj Param high nybble selects horizontal drift: slow right, slow left, fast right, fast left.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .travel
	dw .init_drift
	dw .drift

.travel
	ld a, $4
	call BattleAnim_StepToTarget
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 20
	ret c
	call BattleAnimFunc_BulletSeed_SpawnHit
	ld de, SFX_HEADBUTT
	call PlaySFX
	call BattleAnim_IncAnonJumptableIndex
	ret

.init_drift
	xor a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hli], a
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hli], a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.drift
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 16
	jr nc, .done
	ld e, a

	ld d, 0
	ld hl, .YArc
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a

.check_x
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	swap a
	and $3
	jr z, .slow_right
	cp $1
	jr z, .slow_left
	cp $2
	jr z, .move_right
	jr .move_left

.slow_right
	ld a, e
	and $1
	jr nz, .next_frame
	jr .move_right

.slow_left
	ld a, e
	and $1
	jr nz, .next_frame
	jr .move_left

.move_right
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	inc [hl]
	ld a, [hl]
	jr .set_x

.move_left
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	dec [hl]
	ld a, [hl]

.set_x
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a

.next_frame
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

.YArc:
	db  0, -3, -6, -8, -10, -11, -12, -11
	db -10, -8, -6, -4,  -2,  -1,   0,   1

BattleAnimFunc_SilverWind:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .move

.init
	call .GetPath
	ld a, [hli]
	ld e, a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add e
	ld e, a
	ldh a, [hBattleTurn]
	and a
	jr z, .got_y
	ld hl, BATTLEANIMSTRUCT_FIX_Y
	add hl, bc
	ld a, [hl]
	sub e
	sub 12
	ld e, a
.got_y
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], e
	ldh a, [hBattleTurn]
	and a
	jr z, .got_init_x
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, (-10 * TILE_WIDTH) + 4
	sub [hl]
	ld [hl], a
.got_init_x
	call .GetPath
	inc hl
	ld a, [hli]
	ld e, a
	ld a, [hli]
	swap a
	ld d, a
	ld a, [hl]
	or d
	ld d, a
	ldh a, [hBattleTurn]
	and a
	jr z, .got_path_params
	set 7, d
.got_path_params
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	call BattleAnim_IncAnonJumptableIndex
	ret

.move
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 72
	jr nc, .done
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	bit 7, e
	jr nz, .move_left
	ld a, [hl]
	add 2
	ld [hl], a
	jr .got_x
.move_left
	ld a, [hl]
	sub 2
	ld [hl], a
.got_x
	ld a, e
	swap a
	and $7
	ld d, a
	push de
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	ld a, e
	and $f
	ld e, a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

.GetPath
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, .Paths
	add hl, de
	ret

.Paths:
; y offset, sine angle, amplitude, angle step
	db -40, $00, 4, 1
	db -28, $10, 5, 1
	db -16, $20, 4, 1
	db  -4, $30, 6, 2
	db   8, $08, 5, 1
	db  20, $18, 6, 1
	db -34, $28, 5, 1
	db  26, $38, 4, 1

BattleAnimFunc_IceChunk:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .fall
	dw .shatter

.init
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $30
	inc hl
	ld [hl], $60
	call BattleAnim_IncAnonJumptableIndex

.fall
	call .ApplyYOffset
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	and $3f
	cp 1
	jr z, .start_shatter
	ret

.start_shatter
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $20
	inc hl
	ld [hl], $0c
	ld de, BATTLE_ANIM_FRAMESET_ICE_CHUNK_SHATTER
	call ReinitBattleAnimFrameset
.shatter
	call .ApplyYOffset
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

.ApplyYOffset
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hli]
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleAnimFunc_StoneEdgeRock:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .rise

.init
	ldh a, [hBattleTurn]
	and a
	jr nz, .player_target
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add 12
	ld [hl], a
	jr .got_start_y
.player_target
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], 72
.got_start_y
	call BattleAnim_IncAnonJumptableIndex
	ret

.rise
	call .MoveUp
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 4
	jr z, .spawn_hit
	cp 24
	jr nc, .done
	ret

.spawn_hit
	call BattleAnimFunc_BulletSeed_SpawnHit
	ret

.done
	call BattleAnimExt_Deinit
	ret

.MoveUp
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub 3
	ld [hl], a
	ret

BattleAnimFunc_ShockWaveOrb:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .move
	ld [hl], $18

.move
	ld a, [hl]
	cp $80
	jr nc, .done
	ld d, a
	add $8
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	call BattleAnim_StepCircle
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_BlockX:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .fall
	dw .bounce_big
	dw .bounce_small
	dw .hold
	dw .flicker

.init
	ldh a, [hBattleTurn]
	and a
	ld a, -96
	jr z, .got_start_y
	ld a, -120
.got_start_y
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.fall
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	add 10
	ld [hl], a
	bit 7, a
	ret nz
	xor a
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.bounce_big
	ld d, 16
	ld e, 4
	call .bounce
	ret c
	jr .bounce_done

.bounce_small
	ld d, 8
	ld e, 6
	call .bounce
	ret c

.bounce_done
	xor a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.bounce
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	push af
	call BattleAnim_Sine
	xor $ff
	inc a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop af
	cp $80
	ret

.hold
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 9
	ret c
	xor a
	ld [hl], a
	inc hl
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.flicker
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 19
	ret c
	xor a
	ld [hli], a
	inc [hl]
	ld a, [hl]
	cp 7
	jp z, BattleAnimExt_Deinit
	and 1
	ld de, BATTLE_ANIM_FRAMESET_BLOCK_X
	jr z, .set_flicker_frameset
	ld de, BATTLE_ANIM_FRAMESET_BLOCK_X_HIDDEN
.set_flicker_frameset
	call ReinitBattleAnimFrameset
	ret

BattleAnimFunc_ForcePalm:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .approach
	dw .pause
	dw .exit

.init
	ldh a, [hBattleTurn]
	and a
	jr z, .got_orientation
	ld hl, BATTLEANIMSTRUCT_OAMFLAGS
	add hl, bc
	set B_OAM_XFLIP, [hl]
.got_orientation
	xor a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.approach
	call .MoveForward
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 8
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.pause
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 6
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.exit
	call .MoveForward
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 12
	ret c
	call BattleAnimExt_Deinit
	ret

.MoveForward
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	add 6
	ld [hl], a
	ret

BattleAnimFunc_AerialCrash:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .approach
	dw .pause
	dw .exit

.init
	ldh a, [hBattleTurn]
	and a
	jr z, .got_orientation
	ld hl, BATTLEANIMSTRUCT_OAMFLAGS
	add hl, bc
	set B_OAM_XFLIP, [hl]
.got_orientation
	xor a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.approach
	call .MoveForward
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 19
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.pause
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 6
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.exit
	call .MoveForward
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 12
	ret c
	call BattleAnimExt_Deinit
	ret

.MoveForward
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	add 7
	ld [hl], a
	ret

DEF METEOR_DIVE_GLOBE_START_YOFFSET EQU -95
DEF METEOR_DIVE_GLOBE_STEP EQU 5
DEF METEOR_DIVE_GLOBE_APPROACH_FRAMES EQU 19
DEF METEOR_DIVE_GLOBE_PAUSE_FRAMES EQU 6
DEF METEOR_DIVE_GLOBE_EXIT_FRAMES EQU 8

BattleAnimFunc_MeteorDiveGlobe:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .approach
	dw .pause
	dw .exit

.init
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], METEOR_DIVE_GLOBE_START_YOFFSET
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.approach
	call .MoveDown
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp METEOR_DIVE_GLOBE_APPROACH_FRAMES
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.pause
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp METEOR_DIVE_GLOBE_PAUSE_FRAMES
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.exit
	ldh a, [hBattleTurn]
	and a
	jr z, .exit_player_turn
	call BattleAnimExt_Deinit
	ret

.exit_player_turn
	call .MoveDown
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp METEOR_DIVE_GLOBE_EXIT_FRAMES
	ret c
	call BattleAnimExt_Deinit
	ret

.MoveDown
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	add METEOR_DIVE_GLOBE_STEP
	ld [hl], a
	ret

DEF LEAF_BLADE_STEP EQU 6
DEF LEAF_BLADE_START_OFFSET EQU 48
DEF LEAF_BLADE_APPROACH_FRAMES EQU 8
DEF LEAF_BLADE_PAUSE_FRAMES EQU 6
DEF LEAF_BLADE_EXIT_FRAMES EQU 12
DEF LEAF_BLADE_PLAYER_TARGET_Y_ADJUST EQU -4
DEF LEAF_BLADE_CHIP_DURATION EQU 26

BattleAnimFunc_LeafBlade:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .approach
	dw .pause
	dw .exit

.init
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and 1
	ld d, a
	ldh a, [hBattleTurn]
	and a
	jr z, .got_visible_orientation
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add LEAF_BLADE_PLAYER_TARGET_Y_ADJUST
	ld [hl], a
	ld a, d
	xor 1
	ld d, a
.got_visible_orientation
	ld a, d
	and a
	ld de, BATTLE_ANIM_FRAMESET_LEAF_BLADE
	jr z, .got_frameset
	ld de, BATTLE_ANIM_FRAMESET_LEAF_BLADE_FLIPPED
.got_frameset
	call ReinitBattleAnimFrameset
.set_start_offset
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 0, [hl]
	ld a, -LEAF_BLADE_START_OFFSET
	jr z, .store_start_offset
	ld a, LEAF_BLADE_START_OFFSET
.store_start_offset
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hli], a
	xor a
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.approach
	call .Move
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp LEAF_BLADE_APPROACH_FRAMES
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.pause
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp LEAF_BLADE_PAUSE_FRAMES
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.exit
	call .Move
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp LEAF_BLADE_EXIT_FRAMES
	ret c
	call BattleAnimExt_Deinit
	ret

.Move
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 0, [hl]
	ld a, LEAF_BLADE_STEP
	jr z, .got_step
	ld a, -LEAF_BLADE_STEP
.got_step
	ld d, a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a
	ret

BattleAnimFunc_LeafBladeChip:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp LEAF_BLADE_CHIP_DURATION
	jr c, .update
	call BattleAnimExt_Deinit
	ret

.update
	push af
	and a
	jr nz, .got_velocity
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	ld e, a
	ld d, 0
	ld hl, .InitialXVelocities
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
.got_velocity
	pop af
	ld e, a
	ld d, 0
	push af
	ld hl, .YOffsets
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld d, a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	add d
	ld [hl], a
	pop af
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $3
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and a
	ret z
	bit 7, a
	jr nz, .negative
	dec [hl]
	ret

.negative
	inc [hl]
	ret

.InitialXVelocities
	db -3, -2, 0, 2, 3, 3, 3, 3

.YOffsets
	db -2, -4, -5, -6, -7, -7, -7, -7
	db -6, -6, -5, -5, -4, -4, -3, -3
	db -2, -2, -1, -1,  0,  0,  1,  1
	db  2,  2,  3,  3,  4,  4,  5,  5

DEF SUPERPOWER_ROCK_DONE_Y EQU $68
DEF SUPERPOWER_ROCK_DROP_SPEED EQU 5

BattleAnimFunc_SuperpowerRockChip:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .rise
	dw .drop

.init
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	ld e, a
	ld d, 0
	ld hl, .RiseDurations
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.rise
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	push af
	and 1
	call z, .MoveUp
	pop af
	ld d, a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, d
	cp [hl]
	ret c
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.drop
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add SUPERPOWER_ROCK_DROP_SPEED
	ld [hl], a
	cp SUPERPOWER_ROCK_DONE_Y
	ret c
	jr .done

.done
	call BattleAnimExt_Deinit
	ret

.MoveUp
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ret

.RiseDurations:
	db 96, 90, 84, 78, 72
	db 96, 90, 84

BattleAnimFunc_IngrainRoot:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .update

.init
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	add a
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, .RootData
	add hl, de
	ldh a, [hBattleTurn]
	and a
	jr z, .got_side_data
	inc hl
	inc hl
	inc hl
	inc hl
.got_side_data
	ld a, [hli]
	ld e, a
	ld d, 0
	push hl
	call ReinitBattleAnimFrameset
	ld a, e
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld [hl], a
	pop de
	ld a, [de]
	inc de
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld a, [de]
	inc de
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld a, [de]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.update
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp d
	jr z, .done
	jr c, .done
	sub 10
	cp d
	ret nc
	ld a, d
	and 2
	jr z, .show
	ld de, BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_HIDDEN
	call ReinitBattleAnimFrameset
	ret

.show
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld e, [hl]
	ld d, 0
	call ReinitBattleAnimFrameset
	ret

.done
	call BattleAnimExt_Deinit
	ret

.RootData:
	; player frameset, x offset, y offset, lifetime, enemy frameset, x offset, y offset, lifetime
	db BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_2,        14, 18, 126, BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_2,       -14, 18, 126
	db BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_1_XFLIP, -24, -8, 126, BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_1_XFLIP,  24, -8, 126
	db BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_0,        22, -8, 126, BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_0,       -22, -8, 126
	db BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_3_XFLIP, -16, 14, 126, BATTLE_ANIM_FRAMESET_INGRAIN_ROOT_3_XFLIP,  16, 14, 126

BattleAnimFunc_IngrainOrb:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld e, [hl]
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	cp 1
	jr z, .path1
	cp 2
	jr z, .path2

.path0
	ld a, e
	cp 30
	jr nc, .done
	ld a, 24
	sub e
	call .SetXOffset
	ld a, e
	add a
	ld d, 3
	call BattleAnim_Sine
	add -4
	call .SetYOffset
	ret

.path1
	ld a, e
	cp 30
	jr nc, .done
	ld a, -32
	add e
	call .SetXOffset
	ld a, e
	add a
	add $10
	ld d, 2
	call BattleAnim_Sine
	add -6
	call .SetYOffset
	ret

.path2
	ld a, e
	cp 18
	jr nc, .done
	add a
	ld d, a
	ld a, 32
	sub d
	call .SetXOffset
	ld a, e
	add a
	add $20
	ld d, 3
	call BattleAnim_Sine
	add -10
	call .SetYOffset
	ret

.SetXOffset
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

.SetYOffset
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_TauntPlaced:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .done

.init
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	jr z, .thought_head
	cp 1
	jr z, .anger_left
	cp 3
	jr z, .finger_head
; anger right
	ld de, .EnemyTargetAngerRight
	ldh a, [hBattleTurn]
	and a
	jr z, .got_coords
	ld de, .PlayerTargetAngerRight
	jr .got_coords

.anger_left
	ld de, .EnemyTargetAngerLeft
	ldh a, [hBattleTurn]
	and a
	jr z, .got_coords
	ld de, .PlayerTargetAngerLeft
	jr .got_coords

.thought_head
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy_thought_head
	call .UsePlayerThoughtFrameset
	ld de, .PlayerUserHead
	jr .got_coords

.enemy_thought_head
	ld de, .EnemyUserHead
	jr .got_coords

.UsePlayerThoughtFrameset:
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld a, [hl]
	cp BATTLE_ANIM_FRAMESET_TAUNT_THOUGHT_1
	jr z, .thought1_xflip
	cp BATTLE_ANIM_FRAMESET_TAUNT_THOUGHT_LARGE
	jr z, .thought_large_xflip
	cp BATTLE_ANIM_FRAMESET_TAUNT_THOUGHT_HOLD
	jr z, .thought_hold_xflip
	ret

.thought1_xflip
	ld de, BATTLE_ANIM_FRAMESET_TAUNT_THOUGHT_1_XFLIP
	jp ReinitBattleAnimFrameset

.thought_large_xflip
	ld de, BATTLE_ANIM_FRAMESET_TAUNT_THOUGHT_LARGE_XFLIP
	jp ReinitBattleAnimFrameset

.thought_hold_xflip
	ld de, BATTLE_ANIM_FRAMESET_TAUNT_THOUGHT_HOLD_XFLIP
	jp ReinitBattleAnimFrameset

.finger_head
	ld de, .PlayerUserFinger
	ldh a, [hBattleTurn]
	and a
	jr z, .got_coords
	ld de, .EnemyUserFinger
	ld hl, BATTLEANIMSTRUCT_OAMFLAGS
	add hl, bc
	set B_OAM_XFLIP, [hl]

.got_coords
	ld a, [de]
	inc de
	ld h, b
	ld l, c
	push de
	ld de, BATTLEANIMSTRUCT_XCOORD
	add hl, de
	pop de
	ld [hl], a
	ld a, [de]
	ld h, b
	ld l, c
	ld de, BATTLEANIMSTRUCT_YCOORD
	add hl, de
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex

.done
	ret

.PlayerUserHead:
	db 92, 56
.EnemyUserHead:
	db 92, 56
.PlayerUserFinger:
	db 92, 56
.EnemyUserFinger:
	db 92, 56
.EnemyTargetAngerLeft:
	db 116, 28
.EnemyTargetAngerRight:
	db 156, 28
.PlayerTargetAngerLeft:
	db 40, 64
	.PlayerTargetAngerRight:
	db 68, 64

BattleAnimFunc_IronDefenseGlimmer:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .done

.init
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and 3
	add a
	ld e, a
	ld d, 0
	ld hl, .PlayerCoords
	ldh a, [hBattleTurn]
	and a
	jr z, .got_table
	ld hl, .EnemyCoords
.got_table
	add hl, de
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], e
	inc hl
	ld [hl], d
	call BattleAnim_IncAnonJumptableIndex

.done
	ret

.PlayerCoords:
	db 32, 80
	db 64, 80
	db 32, 100
	db 64, 100

.EnemyCoords:
	db 120, 40
	db 152, 40
	db 120, 60
	db 152, 60

BattleAnimFunc_HexMeanLook:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .done

.init
	call BattleAnim_IncAnonJumptableIndex
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add 8
	ld [hl], a

.done
	ret

BattleAnimFunc_HexGhostFlame:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .orbit

.init
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ldh a, [hBattleTurn]
	and a
	jr z, .orbit
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add 8
	ld [hl], a

.orbit
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 160
	jr c, .set_offsets
	call BattleAnimExt_Deinit
	ret

.set_offsets
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, 24
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc a
	ld [hl], a
	ret

BattleAnimFunc_DisarmingVoiceNote:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .move

.init
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7
	ld e, a
	ld d, 0
	ld hl, .Params
	add hl, de
	add hl, de
	ld a, [hli]
	ld e, [hl]
	push de
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	pop de
	ld d, 0
	call ReinitBattleAnimFrameset

.move
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp 72
	jr nc, .done
	inc [hl]
	ld a, $1
	call BattleAnim_StepToTarget
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	bit 0, [hl]
	jr z, .skip_y
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
.skip_y
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, 18
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc a
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

.Params:
	db $00, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_1
	db $0b, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_2
	db $15, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_3
	db $20, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_1
	db $2b, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_2
	db $35, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_3
	db $00, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_1
	db $00, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_1

BattleAnimFunc_DragonDanceOrb:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .update

.init
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld [hl], 1
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	add 8
	ld [hl], a

.update
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 81
	jr c, .set_radius
	call BattleAnimExt_Deinit
	ret

.set_radius
	cp 61
	jr c, .tight_orbit
	sub 60
	sla a
	sla a
	add 24
	ld d, a
	jr .set_offsets

.tight_orbit
	ld d, 24

.set_offsets
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	call .UpdateSpeed
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	sub e
	ld [hl], a
	ret

.UpdateSpeed:
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp 6
	jr z, .increase_speed
	cp 12
	jr z, .increase_speed
	cp 18
	ret nz

.increase_speed
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	inc [hl]
	ret

BattleAnimFunc_FakeOutHand:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .slide
	dw .hold

.init
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and a
	jr z, .left_hand
	ld a, -4
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ld de, BATTLE_ANIM_FRAMESET_ENCORE_HAND
	ldh a, [hBattleTurn]
	and a
	jr nz, .set_frameset
	ld de, BATTLE_ANIM_FRAMESET_ENCORE_HAND_FLIPPED
	jr .set_frameset

.left_hand
	ld a, 4
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ld de, BATTLE_ANIM_FRAMESET_ENCORE_HAND_FLIPPED
	ldh a, [hBattleTurn]
	and a
	jr nz, .set_frameset
	ld de, BATTLE_ANIM_FRAMESET_ENCORE_HAND

.set_frameset
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ret

.slide
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 7
	ret c
	xor a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.hold
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 6
	ret c
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_YawnCloud:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .travel
	dw .wait_delete

.init
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy_user
	ld a, 56
	ld d, 80
	ld e, 1
	jr .set_coords

.enemy_user
	ld a, 136
	ld d, 40
	ld e, -1

.set_coords
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hli], a
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	call BattleAnim_IncAnonJumptableIndex
	ret

.travel
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp 64
	jr nc, .start_flicker
	push af
	add a
	ld d, 8
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop af
	ld d, a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	add e
	ld [hl], a
	ld a, d
	and 3
	jr nz, .skip_extra_x
	ld a, [hl]
	add e
	ld [hl], a

.skip_extra_x
	ld a, d
	and 1
	jr nz, .inc_frame
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ldh a, [hBattleTurn]
	and a
	jr nz, .move_y_down
	dec [hl]
	jr .inc_frame

.move_y_down
	inc [hl]

.inc_frame
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ret

.start_flicker
	xor a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld de, BATTLE_ANIM_FRAMESET_YAWN_CLOUD_FLICKER
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ret

.wait_delete
	ret

BattleAnimFunc_YawnBubble:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .init
	dw .move

.init
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and 3
	ld e, a
	ldh a, [hBattleTurn]
	and a
	jr z, .got_index
	ld a, e
	add 3
	ld e, a

.got_index
	ld d, 0
	ld hl, .coords
	add hl, de
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hli], a
	ld [hl], d
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.move
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	cp 32
	jr nc, .delete
	push af
	and 1
	jr nz, .skip_y
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]

.skip_y
	pop af
	and 7
	ret nz
	ret

.delete
	call BattleAnimExt_Deinit
	ret

.coords
	; target opponent, then target player
	db 134, 46
	db 136, 34
	db 138, 22
	db  54, 72
	db  56, 60
	db  58, 48

BattleAnimFunc_SandTombFleck:
; Flame Wheel-style circle with upward drift, centered on the target.
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	inc [hl]
	inc [hl]
	ld a, [hl]
	and $7
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $e8
	jr z, .delete
	dec [hl]
	ret

.delete
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_Recover:
; Obj moves in an ever shrinking circle. Obj Param defines initial position in the circle
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	sla a
	sla a
	sla a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld [hl], $1
.one
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .move
	call BattleAnimExt_Deinit
	ret

.move
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld d, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	xor $1
	ld [hl], a
	ret z
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	dec [hl]
	ret

BattleAnimFunc_ThunderWave:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three

.one
	call BattleAnim_IncAnonJumptableIndex
	ld de, BATTLE_ANIM_FRAMESET_THUNDER_WAVE_EXTRA
	call ReinitBattleAnimFrameset
.zero
.two
	ret

.three
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_Clamp_Encore:
; Claps two objects together, twice. Also used by Encore
; Second object's frameset and position relative to first are both defined via this function
; Obj Param: Distance from center (masked with $7F). Bit 7 flips object horizontally by switching to a different frameset
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
	dw .four
	dw .five
	dw .six

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $10
	jr .got_sine_start

.flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $30
.got_sine_start
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7f
	ld [hl], a
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	bit 7, a
	jr nz, .load_no_inc
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	assert BATTLE_ANIM_FRAMESET_CLAMP + 1 ==  BATTLE_ANIM_FRAMESET_CLAMP_FLIPPED
	assert BATTLE_ANIM_FRAMESET_ENCORE_HAND + 1 == BATTLE_ANIM_FRAMESET_ENCORE_HAND_FLIPPED
	inc a
	jr .reinit

.load_no_inc
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl] ; BATTLE_ANIM_FRAMESET_CLAMP or BATTLE_ANIM_FRAMESET_ENCORE_HAND
.reinit
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $1f
	ret nz
.two
.three
.four
.five
	call BattleAnim_IncAnonJumptableIndex
	ret

.six
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], $1
	ret

BattleAnimFunc_Bite:
; Claps two objects together (vertically), twice
; Second object's frameset and position relative to first are both defined via this function
; Obj Param: Distance from center (masked with $7F). Bit 7 flips object vertically by switching to a different frameset
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and a
	jr z, .run
	dec [hl]
	jr nz, .run
	call BattleAnimExt_Deinit
	ret

.run
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
	dw .four
	dw .five
	dw .six

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], $20
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $10
	jr .got_sine_start

.flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $30
.got_sine_start
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7f
	ld [hl], a

.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	bit 7, a
	jr nz, .flipped2
	ld a, BATTLE_ANIM_FRAMESET_BITE_2
	jr .got_frameset

.flipped2
	ld a, BATTLE_ANIM_FRAMESET_BITE_1
.got_frameset
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	inc [hl]
	ld a, [hl]
	and $1f
	ret nz

.two
.three
.four
.five
	call BattleAnim_IncAnonJumptableIndex
	ret

.six
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], $1
	ret

BattleAnimFunc_DrainLifeBite:
; Claps the Bite object once, then holds until the script clears it.
; Obj Param: Distance from center (masked with $7F). Bit 7 flips object vertically by switching to a different frameset
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .hold

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $10
	jr .got_sine_start

.flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $30
.got_sine_start
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7f
	ld [hl], a

.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	bit 7, a
	jr nz, .flipped2
	ld a, BATTLE_ANIM_FRAMESET_BITE_2
	jr .got_frameset

.flipped2
	ld a, BATTLE_ANIM_FRAMESET_BITE_1
.got_frameset
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	inc [hl]
	ld a, [hl]
	and $1f
	ret nz
	call BattleAnim_IncAnonJumptableIndex
	ret

.hold
	ret

BattleAnimFunc_VampirismBite:
; Claps the Vampirism fang objects once, then holds until the script clears them.
; Obj Param: Distance from center (masked with $7F). Bit 7 selects the upper fang.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .hold

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $10
	jr .got_sine_start

.flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $30
.got_sine_start
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7f
	ld [hl], a

.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	bit 7, a
	jr nz, .flipped2
	ld de, BATTLE_ANIM_FRAMESET_VAMPIRISM_FANGS_LOWER
	jr .got_frameset

.flipped2
	ld de, BATTLE_ANIM_FRAMESET_VAMPIRISM_FANGS_UPPER
.got_frameset
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	inc [hl]
	ld a, [hl]
	and $1f
	ret nz
	call BattleAnim_IncAnonJumptableIndex
	ret

.hold
	ret

BattleAnimFunc_SolarBeam:
; Solar Beam charge up animation
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	call BattleAnim_AdjustChargeYCoord
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $28
	inc hl
	ld [hl], $0
.one
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld d, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .zero_radius
	ld d, a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld e, [hl]
	ld hl, -$80
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], d
	ret

.zero_radius
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_ChargeCenter:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	call BattleAnim_AdjustChargeYCoord
.one
	ret

BattleAnim_AdjustChargeYCoord:
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, $60
	sub [hl]
	ld [hl], a
	ret

BattleAnimFunc_Gust:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
	dw .four

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld [hl], 0
.one
.three
	call .GustWobble
	ret

.two
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $88
	jr c, .move
	call BattleAnim_IncAnonJumptableIndex
	ret

.four
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $b8
	jr c, .move
	call BattleAnimExt_Deinit
	ret

.move
	call .GustWobble
	; Move horizontally every frame
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	inc [hl]
	ld a, [hl]
	; Move in the vertically every other frame
	and $1
	ret nz
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ret

.GustWobble:
	; Circular movement where width is retrieved from a list, and height is 1/16 of that
	call .GetGustRadius
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	sub $8
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and a
	jr z, .start_wobble
	cp $c2
	jr c, .finish_wobble
.start_wobble
	dec a
	ld [hl], a
	and $7
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	inc [hl]
	ret

.finish_wobble
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hli], a
	ld [hl], a
	ret

.GetGustRadius:
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld e, [hl]
	ld d, 0
	ld hl, .GustOffsets
	add hl, de
	ld d, [hl]
	ret

.GustOffsets:
	db 8, 6, 5, 4, 5, 6, 8, 12, 16

BattleAnimFunc_Absorb:
; Moves object from target to user and disappears when reaches x coord $30. Example: Absorb, Mega Drain, Leech Seed status
; Obj Param: Speed in the X axis
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $30
	jr nc, .move
	call BattleAnimExt_Deinit
	ret

.move
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld e, a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	sub e
	ld [hl], a
	srl e
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
.loop
	inc [hl]
	dec e
	jr nz, .loop
	ret

BattleAnimFunc_Wrap:
; Plays out object frameset. Use anim_incobj to move to next frameset
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two

.one
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld e, [hl]
	assert BATTLE_ANIM_FRAMESET_BIND_1 + 1 == BATTLE_ANIM_FRAMESET_BIND_2 \
		&& BATTLE_ANIM_FRAMESET_BIND_2 + 1 == BATTLE_ANIM_FRAMESET_BIND_3 \
		&& BATTLE_ANIM_FRAMESET_BIND_3 + 1 == BATTLE_ANIM_FRAMESET_BIND_4
	inc e
	inc hl
	ld d, [hl]   ; preserve bank selector
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1 ; Unused?
	add hl, bc
	ld [hl], $8
.zero
.two
	ret

BattleAnimFunc_LeechSeed:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three
.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], $40
	ret

.one
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $20
	jr c, .sprout
	call BattleAnim_StepThrownToTarget
	ret

.sprout
	ld [hl], $40
	ld de, BATTLE_ANIM_FRAMESET_LEECH_SEED_2
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ret

.two
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and a
	jr z, .flutter
	dec [hl]
	ret

.flutter
	call BattleAnim_IncAnonJumptableIndex
	ld de, BATTLE_ANIM_FRAMESET_LEECH_SEED_3
	call ReinitBattleAnimFrameset
.three
	ret

BattleAnim_StepThrownToTarget:
; Inches object towards the opponent's side in a parabola arc defined by the lower and upper nybble of Obj Param
	dec [hl]
	ld d, $20
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_FIX_Y
	add hl, bc
	ld a, [hl]
	add $2
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld h, [hl]
	ld a, h
	and $f
	swap a
	ld l, a
	ld a, h
	and $f0
	swap a
	ld h, a
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], e
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and $1
	ret nz
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ret

BattleAnimFunc_Spikes:
; Object is thrown at target. After $20 frames it stops and waits another $20 frames then disappear
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], $40
	ret

.one
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $20
	jr c, .wait
	call BattleAnim_StepThrownToTarget
	ret

.wait
	call BattleAnim_IncAnonJumptableIndex
.two
	ret

BattleAnimFunc_RazorWind:
	call BattleAnimFunc_MoveInCircle
	; Causes object to skip ahead the circular motion every frame
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	add $f
	ld [hl], a
	ret

BattleAnimFunc_Kick:
; Uses anim_setobj for different kick types
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two   ; Jump Kick, Hi Jump Kick
	dw .three ; Rolling Kick
	dw .four  ; Rolling Kick (continued)

.zero
	ret

.one ; Unused?
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	cp $30
	jr c, .move_down
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], $0
	ret

.move_down
	add $4
	ld [hl], a
	ret

.two
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $98
	ret nc
	inc [hl]
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_OAMFLAGS
	add hl, bc
	set BATTLEANIMSTRUCT_OAMFLAGS_FIX_COORDS_F, [hl]
	ld hl, BATTLEANIMSTRUCT_FIX_Y
	add hl, bc
	ld [hl], $90
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], $2
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ret

.three
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $2c
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], $80
.four
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $98
	ret nc
	inc [hl]
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld d, $8
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleAnimFunc_Egg:
; Used by Egg Bomb and Softboiled
; Obj Param: Defines jumptable starting index
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one ; Egg Bomb start
	dw .two
	dw .three
	dw .four ; ret
	dw .five
	dw .six ; Softboiled obj 1 start
	dw .seven
	dw .eight
	dw .nine
	dw .ten ; ret
	dw .eleven ; Softboiled obj 2 start
	dw .twelve
	dw .thirteen ; ret

.zero
	; Object starts here then jumps to the jumptable index defined by the Obj Param
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $28
	inc hl ; BATTLEANIMSTRUCT_VAR2
	ld [hl], $10
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], a
	ret

.one
	; Initial Egg Bomb arc movement to x coord $40
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $40
	jr nc, .egg_bomb_vertical_wave
	inc [hl]
.egg_bomb_vertical_wave
	call .EggVerticalWaveMotion
	ret

.six
	; Initial Softboiled arc movement to x coord $4b
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $4b
	jr nc, .softboiled_vertical_wave
	inc [hl]
.softboiled_vertical_wave
	call .EggVerticalWaveMotion
	ret

.two
	; Compares the egg's x coord to determine whether to move, wait or end animation
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $88
	jr nc, .egg_bomb_done
	and $f
	jr nz, .egg_bomb_step
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], $10
	call BattleAnim_IncAnonJumptableIndex ; jumps to three
	ret

.egg_bomb_done
	; Increases jumptable index twice to four
	call BattleAnim_IncAnonJumptableIndex
	inc [hl]
	ret

.three
	; Waits in place
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and a
	jr z, .done_waiting
	dec [hl]
	ret

.done_waiting
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	dec [hl]
.egg_bomb_step
	; Moves towards the target
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld e, [hl]
	ld hl, -$80
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], e
	ret

.five
	; Clears Egg Bomb object via anim_incobj
	call BattleAnimExt_Deinit
	ret

.seven
	; Switches Softboiled frameset to egg wobbling
	ld de, BATTLE_ANIM_FRAMESET_EGG_WOBBLE ; Egg wobbling
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ret

.eight
	; Softboiled object waves slightly side to side
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	inc [hl]
	ld d, $2
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

.nine
	; First Softboiled BATTLE_ANIM_OBJ_EGG turns into the bottom half frameset
	ld de, BATTLE_ANIM_FRAMESET_EGG_CRACKED_BOTTOM ; Cracked egg bottom
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], $4
	call BattleAnim_IncAnonJumptableIndex
	ret

.eleven
	; Second Softboiled BATTLE_ANIM_OBJ_EGG
	ld de, BATTLE_ANIM_FRAMESET_EGG_CRACKED_TOP ; Cracked egg top
	call ReinitBattleAnimFrameset
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $40
	ret

.twelve
	; Top half of egg moves upward for $30 frames
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $20
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $30
	jr c, .done_top_shell
	dec [hl]
	ret

.done_top_shell
	call BattleAnim_IncAnonJumptableIndex
.four
.ten
.thirteen
	ret

.EggVerticalWaveMotion:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hli]
	ld d, [hl] ; BATTLEANIMSTRUCT_VAR2
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $3f ; cp 64
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $20
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	sub $8
	ld [hl], a
	ret nz
	xor a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hli], a
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

BattleAnimFunc_MoveUp:
; Moves object up for 41 frames
; Obj Param: Movement speed
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	and a
	jr z, .move
	cp $d8
	jr nc, .move
	call BattleAnimExt_Deinit
	ret

.move
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	sub d
	ld [hl], a
	ret

BattleAnimFunc_Sound:
; Moves object back and forth in one of three angles using a sine behavior and disappear after 8 frames. Used in Growl, Snore and Kinesis
; Obj Param: Used to define object angle. How much to increase from base frameset, which is hardcoded as BATTLE_ANIM_FRAMESET_SOUND_1
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	ldh a, [hBattleTurn]
	and a
	jr z, .got_turn
	; enemy
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	xor $ff
	add $3
	ld [hl], a
.got_turn
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $8 ; duration
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, BATTLE_ANIM_FRAMESET_SOUND_1
	assert BATTLE_ANIM_FRAMESET_SOUND_1 + 1 == BATTLE_ANIM_FRAMESET_SOUND_2 \
		&& BATTLE_ANIM_FRAMESET_SOUND_2 + 1 == BATTLE_ANIM_FRAMESET_SOUND_3
	add [hl]
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
	ret

.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .done_anim
	dec [hl]
	call .SoundWaveMotion
	ret

.done_anim
	call BattleAnimExt_Deinit
	ret

.SoundWaveMotion:
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	inc [hl]
	inc [hl]
	ld d, $10
	call BattleAnim_Sine
	ld d, a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and a
	jr z, .negative
	dec a
	ret z
	; Obj Param 2
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], d
	ret

.negative
	; Obj Param 0
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, d
	xor $ff
	inc a
	ld [hl], a
	ret

BattleAnimFunc_ConfuseRay:
; Creates the Confuse Ray object and moves it across the screen until x coord $80
; Moves horizontally every frame and vertically every 3 frames
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3f
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $80
	rlca
	ld [hl], a
	assert BATTLE_ANIM_FRAMESET_CONFUSE_RAY_1 + 1 == BATTLE_ANIM_FRAMESET_CONFUSE_RAY_2
	add BATTLE_ANIM_FRAMESET_CONFUSE_RAY_1
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
	ret

.one
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	swap a
	ld d, a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	inc [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $80
	ret nc
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and $3
	jr nz, .skip_vertical_movement
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
.skip_vertical_movement
	and $1
	ret nz
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	inc [hl]
	ret

BattleAnimFunc_Dizzy:
; Moves object in a circle where the height is 1/4 the width, with the next frameset from base whether moving left or right. Also used for Nightmare
; Obj Param: Defines starting position in the circle (masked with $80). Bit 7 flips it at the start
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $80
	rlca
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	assert BATTLE_ANIM_FRAMESET_CHICK_1 + 1 ==  BATTLE_ANIM_FRAMESET_CHICK_2
	assert BATTLE_ANIM_FRAMESET_IMP + 1 == BATTLE_ANIM_FRAMESET_IMP_FLIPPED
	add [hl]
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7f
	ld [hl], a
.one
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $10
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	inc [hl]
	and $3f
	jr z, .not_flipped
	and $1f
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	assert BATTLE_ANIM_FRAMESET_CHICK_1 + 1 ==  BATTLE_ANIM_FRAMESET_CHICK_2
	assert BATTLE_ANIM_FRAMESET_IMP + 1 == BATTLE_ANIM_FRAMESET_IMP_FLIPPED
	inc a
	jr .got_frameset

.not_flipped
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl] ; BATTLE_ANIM_FRAMESET_CHICK_1 or BATTLE_ANIM_FRAMESET_IMP
.got_frameset
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
	ret

BattleAnimFunc_Amnesia:
; Creates 3 objects based on Obj Param
; Obj Param: How much to increase from base frameset, which is hardcoded as BATTLE_ANIM_FRAMESET_AMNESIA_1
; anim_incobj is used to DeInit object (used by Present)
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	assert BATTLE_ANIM_FRAMESET_AMNESIA_1 + 1 == BATTLE_ANIM_FRAMESET_AMNESIA_2 \
		&& BATTLE_ANIM_FRAMESET_AMNESIA_2 + 1 == BATTLE_ANIM_FRAMESET_AMNESIA_3
	add BATTLE_ANIM_FRAMESET_AMNESIA_1
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld e, [hl]
	ld d, 0
	ld hl, .AmnesiaOffsets
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
.one
	ret

.two
	; anim_incobj forces obj to deinit
	call BattleAnimExt_Deinit
	ret

.AmnesiaOffsets: ; Hardcoded Y Offsets for each Obj Param
	db $ec, $f8, $00

BattleAnimFunc_FloatUp:
; Object moves horizontally in a sine wave, while also moving up. Also used by Charm and the Nightmare status
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	inc [hl]
	ld d, $4
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld e, [hl]
	lb hl, -1, $a0
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], e
	ret

BattleAnimFunc_Dig:
; Object moves up then down with a wave motion, while also moving away from the user 1 pixel per frame
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec [hl]
	dec [hl]
	ld d, $10
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	inc [hl]
	ret

BattleAnimFunc_String:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .not_param_zero
	; Obj Param 0 flips when used by enemy
	ld hl, BATTLEANIMSTRUCT_OAMFLAGS
	add hl, bc
	set B_OAM_YFLIP, [hl]
.not_param_zero
	assert BATTLE_ANIM_FRAMESET_STRING_SHOT_1 + 1 == BATTLE_ANIM_FRAMESET_STRING_SHOT_2 \
		&& BATTLE_ANIM_FRAMESET_STRING_SHOT_2 + 1 == BATTLE_ANIM_FRAMESET_STRING_SHOT_3
	add BATTLE_ANIM_FRAMESET_STRING_SHOT_1
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
.one
	ret

BattleAnimFunc_Paralyzed:
; Also used by Disable
; Obj Param: When bit 7 is set, frameset is replaced with flipped version. This bit is discarded and object then moves back and forth between position in lower nybble and upper nybble of Param every other frame
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $0
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld e, [hl]
	ld a, e
	and $70
	swap a
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, e
	and $80
	jr nz, .right
	ld a, e
	and $f
	ld [hl], a
	ret

.right
	ld a, e
	and $f
	xor $ff
	inc a
	ld [hl], a
	ld de, BATTLE_ANIM_FRAMESET_PARALYZED_FLIPPED
	call ReinitBattleAnimFrameset
	ret

.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .var1_zero
	dec [hl]
	ret

.var1_zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	xor $ff
	inc a
	ld [hl], a
	ret

BattleAnimFunc_SpiralDescent:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $7
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $28
	jr nc, .delete
	inc [hl]
	ret

.delete
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_PetalDance:
; Object moves downwards in a spiral around the user. Object disappears at y coord $28
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $3
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $28
	jr nc, .end
	inc [hl]
	ret

.end
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_PoisonGas:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .descent

.zero:
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $83
	jr nc, .next
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld d, $18
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	and $1
	ret nz
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	dec [hl]
	ret

.next
	call BattleAnim_IncAnonJumptableIndex
	ret

.descent:
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $7
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $0d
	jr nc, .delete
	inc [hl]
	ret

.delete
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_SmokeFlameWheel:
; Object spins around target while also moving upward until it disappears at x coord $e8
; Obj Param: Defines where the object starts in the circle
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	inc [hl]
	inc [hl]
	ld a, [hl]
	and $7
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $e8
	jr z, .done
	dec [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_SacredFire:
; Moves object in a circle where the height is 1/8 the width, while also moving upward 2 pixels per frame for 24 frames after which it disappears
; Obj Param: Is used internally only
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	inc [hl]
	inc [hl]
	ld a, [hl]
	and $3
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $d0
	jr z, .done
	dec [hl]
	dec [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_PresentSmokescreen:
; Object bounces from user to target and stops at x coord $6c. Uses anim_incobj to clear object
; Obj Param: Defined but not used
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $34
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], $10
.one
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $6c
	jr c, .do_move
	ret

.do_move
	ld a, $2
	call BattleAnim_StepToTarget
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld d, [hl]
	call BattleAnim_Sine
	bit 7, a
	jr nz, .negative
	xor $ff
	inc a
.negative
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	sub $4
	ld [hl], a
	and $1f
	cp $20
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	srl [hl]
	ret

.two
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_Horn:
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three

.zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ret

.one
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $58
	ret nc
	ld a, $2
	call BattleAnim_StepToTarget
	ret

.two
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	cp $20
	jr c, .three
	call BattleAnimExt_Deinit
	ret

.three
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	ld d, $8
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	sra a
	xor $ff
	inc a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	add $8
	ld [hl], a
	ret

BattleAnimFunc_Needle:
; Moves object towards target, either in a straight line or arc. Stops at x coord $84
; Obj Param: Upper nybble defines the index of the jumptable. Lower nybble defines the speed.
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two

.zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	swap a
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], a
	ret

.two
	; Pin Missile needle (arc)
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld d, $10
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	bit 7, a
	jr z, .negative
	ld [hl], a
.negative
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	sub $4
	ld [hl], a
.one
	; Normal needle (line)
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $84
	jr c, .move_to_target
	call BattleAnimExt_Deinit
	ret

.move_to_target
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	call BattleAnim_StepToTarget
	ret

BattleAnimFunc_ThiefPayday:
; Object drops off target and bounces once on the floor
; Obj Param: Defines every how many frames the object moves horizontally
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $28
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	sub $28
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hli]
	ld d, [hl]
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	and [hl]
	jr nz, .var_doesnt_equal_param
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	dec [hl]
.var_doesnt_equal_param
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $3f
	ret nz
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $20
	inc hl
	srl [hl]
	ret

BattleAnimFunc_AbsorbCircle:
; A circle of objects that starts at the target and moves to the user. It expands until x coord $5a and then shrinks. Once radius reaches 0, the object disappears. Also used by Mimic and Conversion2
; Obj Param: Defines the position in the circle the object starts at
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld d, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	inc [hl]
	ld a, [hl]
	and $1
	jr nz, .dont_move_x
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	dec [hl]
.dont_move_x
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $3
	jr nz, .dont_move_y
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ldh a, [hBattleTurn]
	and a
	jr nz, .move_y_opponent
	inc [hl]
	jr .dont_move_y
.move_y_opponent
	dec [hl]
.dont_move_y
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	cp $5a
	jr nc, .increase_radius
	ld a, [hl]
	and a
	jr z, .end
	dec [hl] ; decreases radius
	ret

.increase_radius
	inc [hl]
	ret

.end
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_Conversion:
; A rotating circle of objects centered at a position. It expands for $40 frames and then shrinks. Once radius reaches 0, the object disappears.
; Obj Param: Defines starting point in the circle
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld d, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	cp $40
	jr nc, .shrink
	inc [hl]
	ret

.shrink
	ld a, [hl]
	dec [hl]
	and a
	ret nz
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_Bonemerang:
; Boomerang-like movement from user to target
; Obj Param: Defines position to start at in the circle
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero:
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
.one:
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $30
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	add $8
	ld d, $30
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	inc [hl]
	ret

BattleAnimFunc_Shiny:
; Puts object in a circle formation of radius $10. Also used by Flash and Light Screen
; Obj Param: Defines where the object starts in the circle
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero:
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $10
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $10
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2 ; unused?
	add hl, bc
	ld [hl], $f
.one:
	ret

BattleAnimFunc_SkyAttack:
; Uses anim_incobj to move to next step
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three

.zero
	call BattleAnim_IncAnonJumptableIndex
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy_turn
	ld a, $f0
	jr .got_var1

.enemy_turn
	ld a, $cc
.got_var1
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], a
	ret

.one
	call .SkyAttack_CyclePalette
	ret

.two
; Moves towards target and stops at x coord $84
	call .SkyAttack_CyclePalette
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $84
	ret nc
	ld a, $4
	call BattleAnim_StepToTarget
	ret

.three
; Moves towards target and disappears at x coord $d0
	call .SkyAttack_CyclePalette
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $d0
	jr nc, .done
	ld a, $4
	call BattleAnim_StepToTarget
	ret

.done
	call BattleAnimExt_Deinit
	ret

.SkyAttack_CyclePalette:
; Cycles wOBP0 pallete
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and $7
	inc [hl]
	srl a
	ld e, a
	ld d, 0
	ldh a, [hSGB]
	and a
	jr nz, .sgb
	ld hl, .GBCPals
	jr .got_pals

.sgb
	ld hl, .SGBPals
.got_pals
	add hl, de
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	and [hl]
	ld [wOBP0], a
	ret

.GBCPals:
	db $ff, $aa, $55, $aa
.SGBPals:
	db $ff, $ff, $00, $00

BattleAnimFunc_GrowthSwordsDance:
; Moves object in a circle where the height is 1/8 the width, while also moving upward 2 pixels per frame
; Obj Param: Defines where the object starts in the circle
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $18
	call BattleAnim_Sine
	sra a
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	add [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld d, $18
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	dec [hl]
	dec [hl]
	ret

BattleAnimFunc_StrengthSeismicToss:
; Moves object up for $e0 frames, then shakes it vertically and throws it at the target. Uses anim_incobj to move to final phase
; Obj Param: Defined but not used
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two

.zero
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $e0
	jr nz, .move_up
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $2
	ret

.move_up
	ld d, a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld e, [hl]
	ld hl, -$80
	add hl, de
	ld e, l
	ld d, h
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], d
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], e
	ret

.one
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	and a
	jr z, .switch_position
	dec [hl]
	ret

.switch_position
	ld [hl], $4
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	xor $ff
	inc a
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	add [hl]
	ld [hl], a
	ret

.two
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $84
	jr nc, .done
	ld a, $4
	call BattleAnim_StepToTarget
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_SpeedLine:
; Used in moves where the user disappears for a speed-based attack such as Quick Attack, Mach Punch and Extremespeed
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $7f
	assert BATTLE_ANIM_FRAMESET_SPEED_LINE_1 + 1 == BATTLE_ANIM_FRAMESET_SPEED_LINE_2 \
		&& BATTLE_ANIM_FRAMESET_SPEED_LINE_2 + 1 == BATTLE_ANIM_FRAMESET_SPEED_LINE_3
	add BATTLE_ANIM_FRAMESET_SPEED_LINE_1
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
.one
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	bit 7, [hl]
	jr nz, .inverted
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	inc [hl]
	ret

.inverted
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	dec [hl]
	ret

BattleAnimFunc_MetronomeHand:
; Fast circular motion with an x radius of $8 and y radius of $2
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	inc [hl]
	push af
	ld d, $2
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop af
	ld d, $8
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleAnimFunc_MetronomeSparkleSketch:
; Sideways wave motion while also moving downward until it disappears at y coord $20
; Obj Param: Only used internally
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $20
	jr c, .do_move
	call BattleAnimExt_Deinit
	ret

.do_move
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $8
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	add $2
	ld [hl], a
	and $7
	ret nz
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	inc [hl]
	ret

BattleAnimFunc_Agility:
; Object moves sideways at a speed determined by Obj Param. Can use anim_incobj to make it disappear
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	add [hl]
	ld [hl], a
	ret

.one
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_SafeguardProtect:
; Moves object in a circle where the width is 1/2 the height
; Obj Param: Defines starting point in circle
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld d, $18
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	sra a
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	inc [hl]
	ret

BattleAnimFunc_LockOnMindReader:
; Moves objects towards a center position
; Obj Param: Used to define object angle from 0 to 3. Lower nybble defines how much to increase from base frameset while upper nybble defines angle of movement. The object moves for $28 frames, then waits for $10 frames and disappears
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $28
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	assert BATTLE_ANIM_FRAMESET_LOCK_ON_1 + 1 == BATTLE_ANIM_FRAMESET_LOCK_ON_2 \
		&& BATTLE_ANIM_FRAMESET_LOCK_ON_2 + 1 == BATTLE_ANIM_FRAMESET_LOCK_ON_3 \
		&& BATTLE_ANIM_FRAMESET_LOCK_ON_3 + 1 == BATTLE_ANIM_FRAMESET_LOCK_ON_4
	assert BATTLE_ANIM_FRAMESET_MIND_READER_1 + 1 == BATTLE_ANIM_FRAMESET_MIND_READER_2 \
		&& BATTLE_ANIM_FRAMESET_MIND_READER_2 + 1 == BATTLE_ANIM_FRAMESET_MIND_READER_3 \
		&& BATTLE_ANIM_FRAMESET_MIND_READER_3 + 1 == BATTLE_ANIM_FRAMESET_MIND_READER_4
	add [hl]
	ld e, a
	inc hl
	ld d, [hl]   ; bank selector
	call ReinitBattleAnimFrameset
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and $f0
	or $8
	ld [hl], a
.one
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and a
	jr z, .done
	dec [hl]
	add $8
	ld d, a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

.done
	ld [hl], $10
	call BattleAnim_IncAnonJumptableIndex
.two
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	dec [hl]
	and a
	ret nz
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_HealBellNotes:
; Object moves horizontally in a sine wave, while also moving left every other frame and downwards for $38 frames after which it disappears
; Obj Param: Defines a frameset offset from FRAMESET_24
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.zero
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, BATTLE_ANIM_FRAMESET_MUSIC_NOTE_1
	assert BATTLE_ANIM_FRAMESET_MUSIC_NOTE_1 + 1 == BATTLE_ANIM_FRAMESET_MUSIC_NOTE_2 \
		&& BATTLE_ANIM_FRAMESET_MUSIC_NOTE_2 + 1 == BATTLE_ANIM_FRAMESET_MUSIC_NOTE_3
	add [hl]
	ld e, a
	ld d, 0
	call ReinitBattleAnimFrameset
.one
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $38
	jr nc, .done
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld d, $18
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	ld a, [hl]
	and $1
	ret nz
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	dec [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_BatonPass:
; Object falls vertically and bounces on the ground
; Obj Param: Defines speed and duration
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and a
	ret z
	ld d, a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	inc [hl]
	call BattleAnim_Sine
	bit 7, a
	jr nz, .negative
	xor $ff
	inc a
.negative
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	and $1f
	ret nz
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	srl [hl]
	ret

BattleAnimFunc_EncoreBellyDrum:
; Object moves at an arc for 8 frames and disappears
; Obj Param: Defines starting position in the arc
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $10
	jr nc, .done
	inc [hl]
	inc [hl]
	ld d, a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_SwaggerMorningSun:
; Moves object at an angle
; Obj Param: Lower 6 bits define angle of movement and upper 2 bits define speed
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld e, [hl]
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld d, [hl]
	ld a, e
	and $c0
	rlca
	rlca
	add [hl]
	ld [hl], a
	ld a, e
	and $3f
	push af
	push de
	call BattleAnim_Sine
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleAnimFunc_HiddenPower:
; Moves object in a ring around position. Uses anim_incobj to move to second phase, where it expands the radius 8 pixels at a time for 13 frames and then disappears
; Obj Param: Defines starting position in circle
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two

.zero
	ld d, $18
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	inc [hl]
	jr .step_circle

.one
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld [hl], $18
.two
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $80
	jr nc, .done
	ld d, a
	add $8
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	jr .step_circle

.done
	call BattleAnimExt_Deinit
	ret

.step_circle
	call BattleAnim_StepCircle
	ret

BattleAnimFunc_Curse:
; Object moves down and to the left 2 pixels at a time until it reaches x coord $30 and disappears
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one

.one
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	ld a, [hl]
	cp $30
	jr c, .done
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	dec [hl]
	dec [hl]
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
	inc [hl]
	inc [hl]
	ret

.done
	call BattleAnimExt_Deinit
.zero:
	ret

BattleAnimFunc_PerishSong:
; Moves object in a large circle with a x radius of $50 and a y radius 1/4 or that, while also moving downwards
; Obj Param: Defines starting position in the circle
	ld d, $50
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	inc [hl]
	inc [hl]
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	add [hl]
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleAnimFunc_RapidSpin:
; Object moves upwards 4 pixels per frame until it disappears at y coord $d0
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $d0
	jr z, .done
	dec [hl]
	dec [hl]
	dec [hl]
	dec [hl]
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnimFunc_BetaPursuit:
; Working but unused animation
; Object moves either down or up 4 pixels per frame, depending on Obj Param. Object disappears after 23 frames when going down, or at y coord $d8 when going up
; Obj Param: 0 moves downwards, 1 moves upwards
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three

.zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .move_up
	call BattleAnim_IncAnonJumptableIndex
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], $ec
.one
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $4
	jr z, .three
	inc [hl]
	inc [hl]
	inc [hl]
	inc [hl]
	ret

.three
	call BattleAnimExt_Deinit
	ret

.move_up
	call BattleAnim_IncAnonJumptableIndex
	call BattleAnim_IncAnonJumptableIndex
.two
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	cp $d8
	ret z
	dec [hl]
	dec [hl]
	dec [hl]
	dec [hl]
	ret

BattleAnimFunc_RainSandstorm:
; Object moves down 4 pixels at a time and right a variable distance
; Obj Param: Defines variation in the movement
;            $0: 2 pixels horizontal movement
;            $1: 8 pixels horizontal movement
;            $2: 4 pixels horizontal movement
	call BattleAnim_AnonJumptable
.anon_dw
	dw .zero
	dw .one
	dw .two
	dw .three

.zero
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld [hl], a
	call BattleAnim_IncAnonJumptableIndex
	ret

.one ; Obj Param 0
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	add $4
	cp $70
	jr c, .dont_reset_y_offset_one
	xor a
.dont_reset_y_offset_one
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	inc [hl]
	inc [hl]
	ret

.two ; Obj Param 1
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	add $4
	cp $70
	jr c, .dont_reset_y_offset_two
	xor a
.dont_reset_y_offset_two
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	add $8
	ld [hl], a
	ret

.three ; Obj Param 2
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld a, [hl]
	add $4
	cp $70
	jr c, .dont_reset_y_offset_three
	xor a
.dont_reset_y_offset_three
	ld [hl], a
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld a, [hl]
	add $4
	ld [hl], a
	ret

BattleAnimFunc_PsychUp:
; Object moves in a circle
; Obj Param: Defines starting position in the circle
	ld d, $18
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld a, [hl]
	inc [hl]
	call BattleAnim_StepCircle
	ret

BattleAnimFunc_Cotton:
; Object moves in a circle slowly
; Obj Param: Defines starting position in the circle
	ld d, $18
	ld hl, BATTLEANIMSTRUCT_VAR2
	add hl, bc
	ld a, [hl]
	inc [hl]
	srl a
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	add [hl]
	call BattleAnim_StepCircle
	ret

BattleAnimFunc_AncientPower:
; Object moves up and down in an arc for $20 frames and then disappears
; Obj Param: Defines range of arc motion
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld a, [hl]
	cp $20
	jr nc, .done
	inc [hl]
	ld hl, BATTLEANIMSTRUCT_PARAM
	add hl, bc
	ld d, [hl]
	call BattleAnim_Sine
	xor $ff
	inc a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	ret

.done
	call BattleAnimExt_Deinit
	ret

BattleAnim_StepCircle:
; Inches object in a circular movement where its height is 1/4 the width
	push af
	push de
	call BattleAnim_Sine
	sra a
	sra a
	ld hl, BATTLEANIMSTRUCT_YOFFSET
	add hl, bc
	ld [hl], a
	pop de
	pop af
	call BattleAnim_Cosine
	ld hl, BATTLEANIMSTRUCT_XOFFSET
	add hl, bc
	ld [hl], a
	ret

BattleAnim_StepToTarget:
; Inches object towards the opponent's side, moving half as much in the Y axis as it did in the X axis. Uses lower nybble of A
	and $f
	ld e, a
	ld hl, BATTLEANIMSTRUCT_XCOORD
	add hl, bc
	add [hl]
	ld [hl], a
	srl e
	ret z
	ld hl, BATTLEANIMSTRUCT_YCOORD
	add hl, bc
.loop
	dec [hl]
	dec e
	jr nz, .loop
	ret

BattleAnim_AnonJumptable:
	pop de
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	ld l, [hl]
	ld h, $0
	add hl, hl
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jp hl

BattleAnim_IncAnonJumptableIndex:
	ld hl, BATTLEANIMSTRUCT_JUMPTABLE_INDEX
	add hl, bc
	inc [hl]
	ret

BattleAnim_Cosine:
; a = d * cos(a * pi/32)
	add %010000 ; cos(x) = sin(x + pi/2)
	; fallthrough
BattleAnim_Sine:
; a = d * sin(a * pi/32)
	calc_sine_wave BattleAnimSineWave

BattleAnim_Sine_e:
	ld a, e
	call BattleAnim_Sine
	ld e, a
	ret

BattleAnim_Cosine_e:
	ld a, e
	call BattleAnim_Cosine
	ld e, a
	ret

BattleAnim_AbsSinePrecise: ; unreferenced
	ld a, e
	call BattleAnim_Sine
	ld e, l
	ld d, h
	ret

BattleAnim_AbsCosinePrecise: ; unreferenced
	ld a, e
	call BattleAnim_Cosine
	ld e, l
	ld d, h
	ret

BattleAnimSineWave:
	sine_table 32
