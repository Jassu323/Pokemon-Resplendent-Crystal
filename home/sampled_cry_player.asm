StartSampledCryAsync::
; Start a minmax2-compressed sampled cry on CH3 and return immediately.
; input: a = sample bank, de = sample header in that bank, c = timer/CH3 block period
	di
	ld b, SAMPLED_CRY_STARTUP_PREFILL_BLOCKS
	call SampledCry_PrepareCacheFromHeader
	jr nc, .done
	call SampledCry_ArmCachedPlayback
.done
	ei
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
	ld [wSampledCryFillBlocksRemaining], a

.next_batch
	ld a, [wSampledCryFillBlocksRemaining]
	and a
	ret z
	cp SAMPLED_CRY_PAIR_STAGE_BLOCKS + 1
	jr c, .requested_count_ready
	ld a, SAMPLED_CRY_PAIR_STAGE_BLOCKS
.requested_count_ready
	ld c, a

	ld a, [wSampledCryCompressedBlocks + 1]
	and a
	jr nz, .check_cache_space
	ld a, [wSampledCryCompressedBlocks]
	cp c
	jr nc, .check_cache_space
	ld c, a

.check_cache_space
	ld a, [wSampledCryCacheCount]
	ld b, a
	ld a, SAMPLED_CRY_MAX_DECODED_BLOCKS
	sub b
	cp c
	jr nc, .batch_count_ready
	ld c, a
.batch_count_ready
	ld a, c
	and a
	ret z
	ld [wSampledCryStagedBlocks], a

	ld a, [wSampledCryCompressedAddress]
	ld l, a
	ld a, [wSampledCryCompressedAddress + 1]
	ld h, a
	ld de, wSampledCryCompressedStaging
	ld a, [wSampledCryStagedBlocks]
	ld b, a
.stage_block
	push bc
	ld c, SAMPLED_CRY_COMPRESSED_BLOCK_SIZE
.stage_byte
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .stage_byte
	pop bc
	dec b
	jr nz, .stage_block

	ld a, l
	ld [wSampledCryCompressedAddress], a
	ld a, h
	ld [wSampledCryCompressedAddress + 1], a

	ld a, [wSampledCryStagedBlocks]
	ld c, a
	ld hl, wSampledCryCompressedBlocks
	ld a, [hl]
	sub c
	ld [hli], a
	jr nc, .subtract_requested
	dec [hl]

.subtract_requested
	ld hl, wSampledCryFillBlocksRemaining
	ld a, [hl]
	sub c
	ld [hl], a

	ldh a, [hROMBank]
	push af
	ld a, BANK(SampledCryMinMax2PairLookup)
	rst Bankswitch
	call SampledCry_DecodePairBatch
	pop af
	rst Bankswitch
	jr .next_batch

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
