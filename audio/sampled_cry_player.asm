StartSampledCryAsync::
; Start a minmax2-compressed sampled cry on CH3 and return immediately.
; input: a = sample bank, de = sample header in that bank, c = timer/CH3 block period
	di
	push bc
	push af
	push de
	ldh a, [hSampledCryTimer]
	and a
	jr z, .no_active_sampled_cry
	call StopSampledCryAsync_NoInterruptControl

.no_active_sampled_cry
	pop de
	pop af
	ldh [hSampledCryBank], a
	ldh [hROMBank], a
	ld [rROMB], a

	ld h, d
	ld l, e
	ld a, [hli]
	ld c, a
	ldh [hSampledCryBlocks], a
	ld a, [hli]
	ld b, a
	ldh [hSampledCryBlocks + 1], a
	or c
	jr nz, .has_blocks
	pop bc
	jr .done_empty

.has_blocks

	ld a, l
	ldh [hSampledCryAddress], a
	ld a, h
	ldh [hSampledCryAddress + 1], a
	pop bc

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

	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryDecodedBuffer)
	ldh [rSVBK], a
	ld a, c
	ld [wSampledCryBlockPeriod], a
	call SampledCry_InitRollingCache
	ld b, SAMPLED_CRY_MAX_DECODED_BLOCKS
	call SampledCry_FillRollingCache

	ld a, LOW(wSampledCryDecodedBuffer)
	ldh [hSampledCryAddress], a
	ld a, HIGH(wSampledCryDecodedBuffer)
	ldh [hSampledCryAddress + 1], a

	ld a, [wSampledCryCacheCount]
	and a
	jr z, .cached_no_blocks
	call SampledCry_CopyNextCachedBlock
	call SampledCry_RestartCH3
	call SampledCry_EnableOutput
	call SampledCry_DecrementCacheCount
	call SampledCry_DecrementRemainingBlocks

.cached_no_blocks
	ldh a, [rIE]
	or IE_VBLANK | IE_TIMER
	ldh [rIE], a
	call SampledCry_StartBlockTimer
	pop af
	ldh [rSVBK], a

.done_empty
	ei
	ret

StopSampledCryAsync::
	di
	ldh a, [hSampledCryTimer]
	and a
	jr z, .done
	call StopSampledCryAsync_NoInterruptControl

.done
	ei
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

SampledCry_ServiceAsync::
	ldh a, [hSampledCryTimer]
	and a
	ret z

	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryDecodedBuffer)
	ldh [rSVBK], a
	ld b, SAMPLED_CRY_CACHE_REFILL_BLOCKS
	call SampledCry_FillRollingCache
	pop af
	ldh [rSVBK], a
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

SampledCry_CanFillRollingCache:
	ld a, [wSampledCryCompressedBlocks]
	ld c, a
	ld a, [wSampledCryCompressedBlocks + 1]
	or c
	ret z

	ld a, [wSampledCryCacheCount]
	cp SAMPLED_CRY_MAX_DECODED_BLOCKS
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
	ld hl, MinMax2BitLevels
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
	ld a, [wCryTracks]
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

MinMax2BitLevels:
for minlevel, 0, 16
	for maxlevel, 0, 16
		if maxlevel >= minlevel
			db minlevel, minlevel + (((maxlevel - minlevel) + 1) / 3), minlevel + (((maxlevel - minlevel) * 2 + 1) / 3), maxlevel
		else
			db minlevel, minlevel, minlevel, minlevel
		endc
	endr
endr
