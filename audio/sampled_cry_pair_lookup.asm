; Expand two packed min/max selectors with one lookup. Compressed refill batches
; are staged in WRAMX4 so this bank only needs to be selected once per batch.

MACRO sampled_cry_pair_row
	db ((\1) << 4) | (\1), ((\1) << 4) | (\2), ((\1) << 4) | (\3), ((\1) << 4) | (\4)
	db ((\2) << 4) | (\1), ((\2) << 4) | (\2), ((\2) << 4) | (\3), ((\2) << 4) | (\4)
	db ((\3) << 4) | (\1), ((\3) << 4) | (\2), ((\3) << 4) | (\3), ((\3) << 4) | (\4)
	db ((\4) << 4) | (\1), ((\4) << 4) | (\2), ((\4) << 4) | (\3), ((\4) << 4) | (\4)
ENDM

SECTION "Sampled Cry Pair Lookup", ROMX, ALIGN[12]

SampledCryMinMax2PairLookup::
for minlevel, 0, 16
	for maxlevel, 0, 16
		if maxlevel >= minlevel
			sampled_cry_pair_row \
				minlevel, \
				minlevel + (((maxlevel - minlevel) + 1) / 3), \
				minlevel + (((maxlevel - minlevel) * 2 + 1) / 3), \
				maxlevel
		else
			sampled_cry_pair_row minlevel, minlevel, minlevel, minlevel
		endc
	endr
endr
SampledCryMinMax2PairLookupEnd::

	assert (SampledCryMinMax2PairLookup & $fff) == 0
	assert SampledCryMinMax2PairLookupEnd - SampledCryMinMax2PairLookup == $1000

SampledCry_DecodePairBatch::
; Decode wSampledCryStagedBlocks staged blocks into the rolling cache.
; The pair-lookup bank and sampled-cry WRAM bank must already be selected.
	ld bc, wSampledCryCompressedStaging
	ld a, [wSampledCryCacheWriteAddress]
	ld e, a
	ld a, [wSampledCryCacheWriteAddress + 1]
	ld d, a

.block_loop
	call .decode_block
	ld a, e
	cp LOW(wSampledCryDecodedBufferEnd)
	jr nz, .increment_cache
	ld a, d
	cp HIGH(wSampledCryDecodedBufferEnd)
	jr nz, .increment_cache
	ld de, wSampledCryDecodedBuffer

.increment_cache
	ld hl, wSampledCryCacheCount
	inc [hl]
	ld hl, wSampledCryStagedBlocks
	dec [hl]
	jr nz, .block_loop

	ld a, e
	ld [wSampledCryCacheWriteAddress], a
	ld a, d
	ld [wSampledCryCacheWriteAddress + 1], a
	ret

.decode_block
; BC = one staged header/selector block; DE = 16-byte decoded destination.
	ld a, [bc]
	inc bc
	push bc
	ld c, a
	and $f0
	swap a
	add HIGH(SampledCryMinMax2PairLookup)
	ld h, a
	ld a, c
	and $0f
	swap a
	ld l, a
	pop bc

rept 8
	ld a, [bc]
	inc bc
	push bc
	ld c, a

	ld a, l
	and $f0
	ld l, a
	ld a, c
	swap a
	and $0f
	or l
	ld l, a
	ld a, [hl]
	ld [de], a
	inc de

	ld a, l
	and $f0
	ld l, a
	ld a, c
	and $0f
	or l
	ld l, a
	ld a, [hl]
	ld [de], a
	inc de

	pop bc
endr
	ret

	assert BANK(SampledCry_DecodePairBatch) == BANK(SampledCryMinMax2PairLookup)

PURGE sampled_cry_pair_row
