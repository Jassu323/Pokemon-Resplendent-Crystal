InitSampledCryMinMax2BitLevels::
	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryMinMax2BitLevels)
	ldh [rSVBK], a
	ld a, BANK(MinMax2BitLevels)
	ld hl, MinMax2BitLevels
	ld de, wSampledCryMinMax2BitLevels
	ld bc, SAMPLED_CRY_MINMAX2_BIT_LEVELS_SIZE
	call FarCopyBytes
	pop af
	ldh [rSVBK], a
	ret

StartSampledCryAsync::
; Start a minmax2-compressed sampled cry on CH3 and return immediately.
; input: a = sample bank, de = sample header in that bank, c = timer/CH3 block period
	ld b, a
	ld a, [wBattleMode]
	and a
	jr z, .normal_start
	ldh a, [hSampledCryTimer]
	and a
	jr nz, .clear_prepared
	ld a, [wPreparedSampledCryState]
	and a
	jr z, .normal_start
	ld a, [wPreparedSampledCryBank]
	cp b
	jr nz, .clear_prepared
	ld a, [wPreparedSampledCryHeader]
	cp e
	jr nz, .clear_prepared
	ld a, [wPreparedSampledCryHeader + 1]
	cp d
	jr nz, .clear_prepared
	ld a, [wPreparedSampledCryPeriod]
	cp c
	jr nz, .clear_prepared
	di
	ld a, b
	ldh [hSampledCryBank], a
	call SampledCry_ArmCachedPlayback
	call ClearBattlePreparedSampledCry
	ei
	ret

.clear_prepared
	call ClearBattlePreparedSampledCry

.normal_start
	ld a, b
	di
	ld b, SAMPLED_CRY_STARTUP_PREFILL_BLOCKS
	call SampledCry_PrepareCacheFromHeader
	jr nc, .done
	call SampledCry_ArmCachedPlayback
.done
	ei
	ret

PrepareBattleSampledCry::
; Prepare a sampled cry cache for battle intro/send-out animations.
; input: a = species
	push hl
	push de
	push bc
	push af
	call LoadCry
	jr nc, .clear
	and a
	jr z, .clear
	ldh a, [hSampledCryAddress]
	ld e, a
	ldh a, [hSampledCryAddress + 1]
	ld d, a
	ldh a, [hSampledCryBank]
	ld c, SAMPLED_CRY_BLOCK_PERIOD_NORMAL
	call PrepareSampledCryForBattleAsync
	jr .done

.clear
	call ClearBattlePreparedSampledCry

.done
	pop af
	pop bc
	pop de
	pop hl
	ret

PrepareSampledCryForBattleAsync:
; input: a = sample bank, de = sample header, c = timer/CH3 block period
	ld [wPreparedSampledCryBank], a
	ld a, e
	ld [wPreparedSampledCryHeader], a
	ld a, d
	ld [wPreparedSampledCryHeader + 1], a
	ld a, c
	ld [wPreparedSampledCryPeriod], a
	xor a
	ld [wPreparedSampledCryFrameCounter], a
	di
	ld b, SAMPLED_CRY_BATTLE_PREFILL_BLOCKS
	ld a, [wPreparedSampledCryBank]
	call SampledCry_PrepareCacheFromHeader
	jr nc, .failed
	ld a, 1
	ld [wPreparedSampledCryState], a
	ei
	ret

.failed
	call ClearBattlePreparedSampledCry
	ei
	ret

ClearBattlePreparedSampledCry::
	xor a
	ld [wPreparedSampledCryState], a
	ret

ServicePreparedBattleSampledCryAsync::
	ld a, [wBattleMode]
	and a
	ret z
	ld a, [wPreparedSampledCryState]
	and a
	ret z
	ldh a, [hSampledCryTimer]
	and a
	ret nz
	ld hl, wPreparedSampledCryFrameCounter
	inc [hl]
	ld a, [hl]
	cp SAMPLED_CRY_PREPARED_REFILL_FRAMES
	ret c
	xor a
	ld [hl], a

	ldh a, [hROMBank]
	push af
	ld a, [wPreparedSampledCryBank]
	rst Bankswitch

	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryDecodedBuffer)
	ldh [rSVBK], a
	ld b, SAMPLED_CRY_CACHE_REFILL_BLOCKS
	call SampledCry_FillRollingCache
	pop af
	ldh [rSVBK], a

	pop af
	rst Bankswitch
	ret

SampledCry_PrepareCacheFromHeader:
; input: a = sample bank, de = sample header, b = prefill blocks, c = timer/CH3 block period
	ldh [hSampledCryBank], a
	ldh a, [hROMBank]
	push af
	push bc
	ld h, d
	ld l, e
	ldh a, [hSampledCryTimer]
	and a
	jr z, .no_active_sampled_cry
	call StopSampledCryAsync_NoInterruptControl

.no_active_sampled_cry
	ldh a, [hSampledCryBank]
	rst Bankswitch

	ld a, [hli]
	ld c, a
	ldh [hSampledCryBlocks], a
	ld a, [hli]
	ld b, a
	ldh [hSampledCryBlocks + 1], a
	or c
	jr nz, .has_blocks
	pop bc
	pop af
	rst Bankswitch
	and a
	ret

.has_blocks
	ld a, l
	ldh [hSampledCryAddress], a
	ld a, h
	ldh [hSampledCryAddress + 1], a
	pop bc

	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryDecodedBuffer)
	ldh [rSVBK], a
	ld a, c
	ld [wSampledCryBlockPeriod], a
	call SampledCry_InitRollingCache
	call SampledCry_FillRollingCache
	pop af
	ldh [rSVBK], a
	pop af
	rst Bankswitch
	scf
	ret

SampledCry_ArmCachedPlayback:
	ldh a, [rAUDVOL]
	ldh [hSampledCrySavedAUDVOL], a
	ldh a, [rAUDTERM]
	ldh [hSampledCrySavedAUDTERM], a
	ldh a, [rAUD3ENA]
	ldh [hSampledCrySavedAUD3ENA], a
	ldh a, [rAUD3LEN]
	ldh [hSampledCrySavedAUD3LEN], a
	ldh a, [rAUD3LEVEL]
	ldh [hSampledCrySavedAUD3LEVEL], a
	ldh a, [rAUD3LOW]
	ldh [hSampledCrySavedAUD3LOW], a
	ldh a, [rAUD3HIGH]
	ldh [hSampledCrySavedAUD3HIGH], a
	ldh a, [rIE]
	ldh [hSampledCrySavedIE], a
	ldh a, [rTAC]
	ldh [hSampledCrySavedTAC], a
	ldh a, [rTMA]
	ldh [hSampledCrySavedTMA], a
	ldh a, [rTIMA]
	ldh [hSampledCrySavedTIMA], a

	ld a, 1
	ldh [hSampledCryTimer], a
	ld a, AUDENA_ON
	ldh [rAUDENA], a
	call SampledCry_EnableOutput

	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryDecodedBuffer)
	ldh [rSVBK], a
	ld a, LOW(wSampledCryDecodedBuffer)
	ldh [hSampledCryAddress], a
	ld a, HIGH(wSampledCryDecodedBuffer)
	ldh [hSampledCryAddress + 1], a

	ld a, [wSampledCryCacheCount]
	and a
	jr z, .cached_no_blocks
	call SampledCry_CopyNextCachedBlock
	call SampledCry_RestartCH3
	call SampledCry_DecrementCacheCount
	call SampledCry_DecrementRemainingBlocks

.cached_no_blocks
	ldh a, [rIE]
	or IE_VBLANK | IE_TIMER
	ldh [rIE], a
	call SampledCry_StartBlockTimer
	pop af
	ldh [rSVBK], a
	ret

SampledCry_AsyncTimerTick::
	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryDecodedBuffer)
	ldh [rSVBK], a

	ldh a, [hSampledCryBlocks]
	ld c, a
	ldh a, [hSampledCryBlocks + 1]
	ld b, a
	or c
	jr nz, .has_remaining_block
	pop af
	ldh [rSVBK], a
	jp StopSampledCryAsync_NoInterruptControl

.has_remaining_block
	ld a, [wSampledCryCacheCount]
	and a
	jr nz, .has_decoded_block
	pop af
	ldh [rSVBK], a
	jp StopSampledCryAsync_NoInterruptControl

.has_decoded_block
	call SampledCry_CopyNextCachedBlock
	call SampledCry_RestartCH3
	call SampledCry_DecrementCacheCount
	call SampledCry_DecrementRemainingBlocks
	pop af
	ldh [rSVBK], a
	ret

SampledCry_CopyNextCachedBlock::
	ldh a, [hSampledCryAddress]
	ld l, a
	ldh a, [hSampledCryAddress + 1]
	ld h, a

	xor a
	ldh [rAUD3ENA], a
	ld de, rAUD3WAVE_0
	ld c, AUD3WAVE_SIZE
.copy_wave_block
	ld a, [hli]
	ld [de], a
	inc e
	dec c
	jr nz, .copy_wave_block

	ld a, l
	cp LOW(wSampledCryDecodedBufferEnd)
	jr nz, .store_read_pointer
	ld a, h
	cp HIGH(wSampledCryDecodedBufferEnd)
	jr nz, .store_read_pointer
	ld hl, wSampledCryDecodedBuffer

.store_read_pointer
	ld a, l
	ldh [hSampledCryAddress], a
	ld a, h
	ldh [hSampledCryAddress + 1], a
	ret

SampledCry_ServiceAsync::
	ldh a, [hSampledCryTimer]
	and a
	ret z

	ldh a, [hROMBank]
	push af
	ldh a, [hSampledCryBank]
	rst Bankswitch

	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryDecodedBuffer)
	ldh [rSVBK], a
	ld b, SAMPLED_CRY_CACHE_REFILL_BLOCKS
	call SampledCry_FillRollingCache
	pop af
	ldh [rSVBK], a

	pop af
	rst Bankswitch
	ret

SampledCry_InitRollingCache::
	xor a
	ld [wSampledCryCacheCount], a

	ldh a, [hSampledCryBlocks]
	ld [wSampledCryCompressedBlocks], a
	ldh a, [hSampledCryBlocks + 1]
	ld [wSampledCryCompressedBlocks + 1], a

	ldh a, [hSampledCryAddress]
	ld [wSampledCryCompressedAddress], a
	ldh a, [hSampledCryAddress + 1]
	ld [wSampledCryCompressedAddress + 1], a

	ld a, LOW(wSampledCryDecodedBuffer)
	ld [wSampledCryCacheWriteAddress], a
	ld a, HIGH(wSampledCryDecodedBuffer)
	ld [wSampledCryCacheWriteAddress + 1], a
	ret

SampledCry_FillRollingCache::
	ld a, b
	and a
	ret z

.fill_loop
	call SampledCry_CanFillRollingCache
	ret z
	push bc
	call SampledCry_DecodeOneRollingCacheBlock
	pop bc
	dec b
	jr nz, .fill_loop
	ret

SampledCry_DecodeOneRollingCacheBlock:
	ld a, [wSampledCryCompressedAddress]
	ld l, a
	ld a, [wSampledCryCompressedAddress + 1]
	ld h, a

	ld a, [wSampledCryCacheWriteAddress]
	ld e, a
	ld a, [wSampledCryCacheWriteAddress + 1]
	ld d, a

	call SampledCry_DecodeMinMax2BlockToDE

	ld a, l
	ld [wSampledCryCompressedAddress], a
	ld a, h
	ld [wSampledCryCompressedAddress + 1], a

	ld a, e
	cp LOW(wSampledCryDecodedBufferEnd)
	jr nz, .store_write_pointer
	ld a, d
	cp HIGH(wSampledCryDecodedBufferEnd)
	jr nz, .store_write_pointer
	ld de, wSampledCryDecodedBuffer

.store_write_pointer
	ld a, e
	ld [wSampledCryCacheWriteAddress], a
	ld a, d
	ld [wSampledCryCacheWriteAddress + 1], a

	ld hl, wSampledCryCompressedBlocks
	ld a, [hl]
	sub 1
	ld [hli], a
	jr nc, .increment_cache_count
	dec [hl]

.increment_cache_count
	ld hl, wSampledCryCacheCount
	inc [hl]
	ret

SampledCry_DecodeMinMax2BlockToDE::
	ld a, [hli]
	push hl
	push de
	ld c, a
	ld b, 0
	sla c
	rl b
	sla c
	rl b
	ld hl, wSampledCryMinMax2BitLevels
	add hl, bc
	ld a, [hli]
	ld [wSampledCryLevel0], a
	ld a, [hli]
	ld [wSampledCryLevel1], a
	ld a, [hli]
	ld [wSampledCryLevel2], a
	ld a, [hli]
	ld [wSampledCryLevel3], a
	pop de
	pop hl

rept 8
	ld a, [hli]
	ld c, a

	ld a, c
	and %11000000
	rlca
	rlca
	call SampledCry_GetMinMax2Level
	swap a
	ld b, a
	ld a, c
	and %00110000
	swap a
	call SampledCry_GetMinMax2Level
	or b
	ld [de], a
	inc de

	ld a, c
	and %00001100
	rrca
	rrca
	call SampledCry_GetMinMax2Level
	swap a
	ld b, a
	ld a, c
	and %00000011
	call SampledCry_GetMinMax2Level
	or b
	ld [de], a
	inc de
endr
	ret

SampledCry_GetMinMax2Level:
	and %00000011
	jr z, .level0
	dec a
	jr z, .level1
	dec a
	jr z, .level2
	ld a, [wSampledCryLevel3]
	ret

.level0
	ld a, [wSampledCryLevel0]
	ret

.level1
	ld a, [wSampledCryLevel1]
	ret

.level2
	ld a, [wSampledCryLevel2]
	ret

SampledCry_RestartCH3::
; WRAMX bank 4 must be selected.
	ld a, AUD3ENA_ON
	ldh [rAUD3ENA], a
	xor a
	ldh [rAUD3LEN], a
	ld a, AUD3LEVEL_100
	ldh [rAUD3LEVEL], a
	ld a, [wSampledCryBlockPeriod]
	ld c, a
	xor a
	sub c
	ldh [rAUD3LOW], a
	ld a, AUD3HIGH_RESTART | HIGH(SAMPLED_CRY_CH3_PERIOD)
	ldh [rAUD3HIGH], a
	ret


SECTION "Sampled Cry ROM0 Gap", ROM0[$0063]

SampledCry_CanFillRollingCache:
	ld a, [wSampledCryCompressedBlocks]
	ld c, a
	ld a, [wSampledCryCompressedBlocks + 1]
	or c
	ret z

	ld a, [wSampledCryCacheCount]
	cp SAMPLED_CRY_MAX_DECODED_BLOCKS
	ret

StopSampledCryAsync_NoInterruptControl::
	xor a
	ldh [hSampledCryTimer], a
	ldh [hSampledCryBlocks], a
	ldh [hSampledCryBlocks + 1], a
	ldh [rTAC], a
	ldh [rAUD3ENA], a
	call SampledCry_ClearTimerFlag

	ldh a, [hSampledCrySavedTIMA]
	ldh [rTIMA], a
	ldh a, [hSampledCrySavedTMA]
	ldh [rTMA], a
	ldh a, [hSampledCrySavedTAC]
	ldh [rTAC], a
	ldh a, [hSampledCrySavedIE]
	ldh [rIE], a

	ldh a, [hSampledCrySavedAUD3ENA]
	ldh [rAUD3ENA], a
	ldh a, [hSampledCrySavedAUD3LEN]
	ldh [rAUD3LEN], a
	ldh a, [hSampledCrySavedAUD3LEVEL]
	ldh [rAUD3LEVEL], a
	ldh a, [hSampledCrySavedAUD3LOW]
	ldh [rAUD3LOW], a
	ldh a, [hSampledCrySavedAUD3HIGH]
	ldh [rAUD3HIGH], a
	ldh a, [hSampledCrySavedAUDTERM]
	ldh [rAUDTERM], a
	ldh a, [hSampledCrySavedAUDVOL]
	ldh [rAUDVOL], a
	ret

SampledCry_DecrementRemainingBlocks::
	ldh a, [hSampledCryBlocks]
	ld c, a
	ldh a, [hSampledCryBlocks + 1]
	ld b, a
	dec bc
	ld a, c
	ldh [hSampledCryBlocks], a
	ld a, b
	ldh [hSampledCryBlocks + 1], a
	ret

SampledCry_DecrementCacheCount::
	ld hl, wSampledCryCacheCount
	dec [hl]
	ret

SampledCry_StartBlockTimer::
; WRAMX bank 4 must be selected.
	xor a
	ldh [rTAC], a
	ld a, [wSampledCryBlockPeriod]
	ld c, a
	xor a
	sub c
	ldh [rTMA], a
	ldh [rTIMA], a
	call SampledCry_ClearTimerFlag
	ld a, TAC_START | TAC_65KHZ
	ldh [rTAC], a
	ret

SampledCry_ClearTimerFlag::
	ldh a, [rIF]
	res B_IF_TIMER, a
	ldh [rIF], a
	ret

SampledCry_GetAUDTERM:
	ld a, [wStereoPanningMask]
	and a
	jr z, .both
	ld a, [wOptions]
	bit STEREO, a
	jr z, .both
	ld a, [wCryTracks]
	and AUDTERM_3_LEFT | AUDTERM_3_RIGHT
	ret nz

.both
	ld a, AUDTERM_3_LEFT | AUDTERM_3_RIGHT
	ret

SampledCry_EnableOutput:
	ld a, SAMPLED_CRY_MAX_VOLUME
	ldh [rAUDVOL], a
	call SampledCry_GetAUDTERM
	ldh [rAUDTERM], a
	ret
