GetUnownLetter:
; Return Unown letter in wUnownLetter based on DVs at hl

; Take the middle 2 bits of each DV and place them in order:
;	atk  def  spd  spc
;	.ww..xx.  .yy..zz.

	; atk
	ld a, [hl]
	and %01100000
	sla a
	ld b, a
	; def
	ld a, [hli]
	and %00000110
	swap a
	srl a
	or b
	ld b, a

	; spd
	ld a, [hl]
	and %01100000
	swap a
	sla a
	or b
	ld b, a
	; spc
	ld a, [hl]
	and %00000110
	srl a
	or b

; Divide by 10 to get 0-25
	ldh [hDividend + 3], a
	xor a
	ldh [hDividend], a
	ldh [hDividend + 1], a
	ldh [hDividend + 2], a
	ld a, $ff / NUM_UNOWN + 1
	ldh [hDivisor], a
	ld b, 4
	call Divide

; Increment to get 1-26
	ldh a, [hQuotient + 3]
	inc a
	ld [wUnownLetter], a
	ret

GetMonFrontpic:
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call IsAPokemon
	ret c
	ldh a, [rWBK]
	push af
	call _GetFrontpic
	pop af
	ldh [rWBK], a
	jp CloseSRAM

GetAnimatedFrontpic:
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call IsAPokemon
	ret c
	ldh a, [rWBK]
	push af
	xor a
	ldh [hBGMapMode], a
	call _GetFrontpic
	ld a, BANK(vTiles3)
	ldh [rVBK], a
	call GetAnimatedEnemyFrontpic
	xor a
	ldh [rVBK], a
	pop af
	ldh [rWBK], a
	jp CloseSRAM

_GetFrontpic:
	ld a, BANK(sEnemyFrontPicTileCount)
	call OpenSRAM
	push de
	call _PrepareFrontpic
	pop hl
	push hl
	ld de, sPaddedEnemyFrontPic
	ld c, 7 * 7
	ldh a, [hROMBank]
	ld b, a
	call Get2bpp
	pop hl
	ret

_PrepareFrontpic:
	call GetBaseData
	ld a, [wBasePicSize]
	and $f
	push af
	call GetFrontpicBaseTileCount
	push af
	call GetFrontpicPointer
	ld a, b
	call GetFarByte
	ld [sEnemyFrontPicTileCount], a
	inc hl
	push bc
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a
	ld a, b
	ld de, wDecompressScratch
	call FarDecompress
	pop bc
	pop af
	ld c, a
	ld a, [sEnemyFrontPicTileCount]
	sub c
	ld c, a
.tail_loop
	ld a, c
	and a
	jr z, .dictionary_ready
	inc hl
	push bc
	ld a, b
	call FarDecompress
	pop bc
	ld a, c
	sub FRONTPIC_ANIM_DICTIONARY_CHUNK_TILES
	jr nc, .store_remaining
	xor a
.store_remaining
	ld c, a
	jr .tail_loop
.dictionary_ready
	pop bc
	ld hl, sPaddedEnemyFrontPic
	ld de, wDecompressScratch
	jp PadFrontpic

Pokedex_PrepareFrontpicBase::
; Decompress only the native first frame. The remaining independently
; compressed streams are retained as a cancellable Dex animation job. Pad the
; base directly into Dex WRAM0 so selection staging does not round-trip through
; sPaddedEnemyFrontPic.
	call GetBaseData
	ld a, [wBasePicSize]
	and $f
	push af
	call GetFrontpicBaseTileCount
	push af
	call GetFrontpicPointer
	ld a, b
	call GetFarByte
	ld [sEnemyFrontPicTileCount], a
	ld [wPokedexAnimDictionaryTileCount], a
	inc hl
	push bc
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a
	ld a, b
	ld de, wDecompressScratch
	call FarDecompress
	pop bc
	inc hl
	ld a, b
	ld [wPokedexAnimDictionaryBank], a
	ld a, l
	ld [wPokedexAnimDictionaryAddress], a
	ld a, h
	ld [wPokedexAnimDictionaryAddress + 1], a
	ld a, e
	ld [wPokedexAnimDictionaryDestination], a
	ld a, d
	ld [wPokedexAnimDictionaryDestination + 1], a
	pop af
	ld c, a
	ld a, [wPokedexAnimDictionaryTileCount]
	sub c
	ld [wPokedexAnimDictionaryTilesRemaining], a
	ld a, [wCurPartySpecies]
	ld [wPokedexAnimOwner], a
	ld a, [wPokedexAnimDictionaryTilesRemaining]
	and a
	ld a, POKEDEX_ANIM_PRODUCER_PENDING
	jr z, .state_ready
	ld a, POKEDEX_ANIM_PRODUCER_LOADING
.state_ready
	ld [wPokedexAnimProducerState], a
	pop bc
	ld hl, wPokedexWRAM0Scratch
	ld de, wDecompressScratch
	jp PadFrontpic

DEF BATTLE_FRONTPIC_PRODUCER_INACTIVE   EQU 0
DEF BATTLE_FRONTPIC_PRODUCER_BASE_BANK0 EQU 1
DEF BATTLE_FRONTPIC_PRODUCER_BASE_BANK1 EQU 2
DEF BATTLE_FRONTPIC_PRODUCER_DICTIONARY EQU 3

DEF BATTLE_FRONTPIC_TRANSFER_TILES         EQU 8

BattleFrontpicProducer_Start::
; Prepare the current enemy's padded base picture and retain the animation
; dictionary as an incremental battle job. Link data shares this WRAM0 union,
; so link battles deliberately retain the synchronous loader.
	xor a
	ld [wBattleFrontpicProducerState], a
	ld a, [wLinkMode]
	and a
	jr nz, .failed
	ldh a, [hCGB]
	and a
	jr z, .failed
	ldh a, [hDMATransfer]
	and a
	jr nz, .failed
	ld a, [wRequested2bppSize]
	and a
	jr nz, .failed
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call IsAPokemon
	jr c, .failed

	ldh a, [rWBK]
	push af
	xor a
	ldh [hBGMapMode], a
	ld a, BANK(sEnemyFrontPicTileCount)
	call OpenSRAM
	call .PrepareBase
	call CloseSRAM
	pop af
	ldh [rWBK], a

	ld a, [wBattleMenuGFXFlags]
	res BATTLE_MENU_GFX_CLEAN_F, a
	ld [wBattleMenuGFXFlags], a
	xor a
	ldh [rVBK], a
	scf
	ret

.failed
	and a
	ret

.PrepareBase:
	call GetBaseData
	ld a, [wBasePicSize]
	and $f
	push af
	call GetFrontpicBaseTileCount
	push af
	call GetFrontpicPointer
	ld a, b
	call GetFarByte
	ld [sEnemyFrontPicTileCount], a
	inc hl
	push bc
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a
	ld a, b
	ld de, wDecompressScratch
	call FarDecompress
	pop bc
	inc hl
	ld a, b
	ld [wBattleFrontpicProducerBank], a
	ld a, l
	ld [wBattleFrontpicProducerAddress], a
	ld a, h
	ld [wBattleFrontpicProducerAddress + 1], a
	pop af
	ld c, a
	ld a, [sEnemyFrontPicTileCount]
	sub c
	ld [wBattleFrontpicProducerTilesRemaining], a
	xor a
	ld [wBattleFrontpicProducerStagedTiles], a
	ld [wBattleFrontpicProducerStageOffset], a
	ld [wBattleFrontpicProducerTransferBank], a
	ld a, LOW(vTiles5 + 7 * 7 tiles)
	ld [wBattleFrontpicProducerVRAMAddress], a
	ld a, HIGH(vTiles5 + 7 * 7 tiles)
	ld [wBattleFrontpicProducerVRAMAddress + 1], a
	ld a, BATTLE_FRONTPIC_PRODUCER_BASE_BANK0
	ld [wBattleFrontpicProducerState], a
	pop bc
	ld hl, wBattleFrontpicProducerBuffer
	ld de, wDecompressScratch
	jp PadFrontpic

BattleFrontpicProducer_StartOrLoad::
	call BattleFrontpicProducer_Start
	ret c
	ld de, vTiles2
	jp GetAnimatedFrontpic

BattleFrontpicProducer_StartEnemyOrLoad::
; Preserve GetEnemyMonFrontpic's form selection on trainer send-outs.
	ld hl, wEnemyMonDVs
	predef GetUnownLetter
	jp BattleFrontpicProducer_StartOrLoad

BattleFrontpicProducer_Service::
; Frame drivers treat background services as transparent work.
	push hl
	push de
	push bc
	push af
	call .Run
	pop af
	pop bc
	pop de
	pop hl
	ret

.Run
; Produce at most one bounded VRAM transaction for the next frame. A queued
; transaction retains ownership of rVBK until the frame driver restores it.
	ld a, [wBattleFrontpicProducerState]
	and a
	ret z
	ldh a, [hDMATransfer]
	and a
	jr z, .no_pending_transfer
	ld a, [wBattleFrontpicProducerTransferBank]
	ldh [rVBK], a
	ret

.no_pending_transfer
	ld a, [wRequested2bppSize]
	and a
	ret nz
	ld a, [wBattleFrontpicProducerState]
	cp BATTLE_FRONTPIC_PRODUCER_BASE_BANK0
	jr z, .queue_base_bank0
	cp BATTLE_FRONTPIC_PRODUCER_BASE_BANK1
	jr z, .queue_base_bank1

	ld a, [wBattleFrontpicProducerStagedTiles]
	and a
	jr nz, .queue_dictionary
	ld a, [wBattleFrontpicProducerTilesRemaining]
	and a
	jr z, .finished
	call .DecodeDictionaryChunk
	; fallthrough

.queue_dictionary
	call .NormalizeDictionaryDestination
	call .GetDictionaryTransferCount
	push bc
	ld b, c
	ld a, [wBattleFrontpicProducerStagedTiles]
	cp 1
	jr nz, .got_logical_transfer_count
	ld b, 1
.got_logical_transfer_count

	ld a, [wBattleFrontpicProducerStageOffset]
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wBattleFrontpicProducerBuffer
	add hl, de
	push hl

	ld a, [wBattleFrontpicProducerVRAMAddress]
	ld e, a
	ld a, [wBattleFrontpicProducerVRAMAddress + 1]
	ld d, a
	push de

	ld hl, wBattleFrontpicProducerStagedTiles
	ld a, [hl]
	sub b
	ld [hl], a
	ld hl, wBattleFrontpicProducerStageOffset
	ld a, [hl]
	add b
	ld [hl], a

	ld a, b
	swap a
	ld l, a
	and $f
	ld h, a
	ld a, l
	and $f0
	ld l, a
	ld a, [wBattleFrontpicProducerVRAMAddress]
	add l
	ld [wBattleFrontpicProducerVRAMAddress], a
	ld a, [wBattleFrontpicProducerVRAMAddress + 1]
	adc h
	ld [wBattleFrontpicProducerVRAMAddress + 1], a

	pop de
	pop hl
	pop bc
	ld a, BANK(vTiles5)
	jp .QueueTransfer

.queue_base_bank0
	ld a, BATTLE_FRONTPIC_PRODUCER_BASE_BANK1
	ld [wBattleFrontpicProducerState], a
	ld hl, wBattleFrontpicProducerBuffer
	ld de, vTiles2
	ld c, 7 * 7
	xor a
	jp .QueueTransfer

.queue_base_bank1
	ld a, BATTLE_FRONTPIC_PRODUCER_DICTIONARY
	ld [wBattleFrontpicProducerState], a
	ld hl, wBattleFrontpicProducerBuffer
	ld de, vTiles5
	ld c, 7 * 7
	ld a, BANK(vTiles5)
	jp .QueueTransfer

.finished
	xor a
	ld [wBattleFrontpicProducerState], a
	ret

.DecodeDictionaryChunk:
	ld a, [wBattleFrontpicProducerTilesRemaining]
	cp FRONTPIC_ANIM_DICTIONARY_CHUNK_TILES
	jr c, .got_chunk_size
	ld a, FRONTPIC_ANIM_DICTIONARY_CHUNK_TILES
.got_chunk_size
	ld [wBattleFrontpicProducerStagedTiles], a
	ld c, a
	xor a
	ld [wBattleFrontpicProducerStageOffset], a
	ld a, [wBattleFrontpicProducerTilesRemaining]
	sub c
	ld [wBattleFrontpicProducerTilesRemaining], a

	ld a, [wBattleFrontpicProducerAddress]
	ld l, a
	ld a, [wBattleFrontpicProducerAddress + 1]
	ld h, a
	ld a, [wBattleFrontpicProducerBank]
	ld de, wBattleFrontpicProducerBuffer
	call FarDecompress
	inc hl
	ld a, l
	ld [wBattleFrontpicProducerAddress], a
	ld a, h
	ld [wBattleFrontpicProducerAddress + 1], a

	ld a, [wBattleFrontpicProducerStagedTiles]
	ld c, a
	swap a
	and $f0
	ld c, a
	ld hl, wBattleFrontpicProducerBuffer
	ld d, h
	ld e, l
	jp LoadOrientedFrontpic

.NormalizeDictionaryDestination:
	ld a, [wBattleFrontpicProducerVRAMAddress]
	cp LOW(vTiles5 tile $7f)
	ret nz
	ld a, [wBattleFrontpicProducerVRAMAddress + 1]
	cp HIGH(vTiles5 tile $7f)
	ret nz
	ld a, LOW(vTiles4)
	ld [wBattleFrontpicProducerVRAMAddress], a
	ld a, HIGH(vTiles4)
	ld [wBattleFrontpicProducerVRAMAddress + 1], a
	ret

.GetDictionaryTransferCount:
	ld a, [wBattleFrontpicProducerStagedTiles]
	cp BATTLE_FRONTPIC_TRANSFER_TILES + 1
	jr c, .within_transfer_limit
	jr nz, .full_transfer
	; Split nine tiles as seven plus two; hDMATransfer uses zero as idle and
	; therefore cannot represent a one-block queued transfer.
	ld c, BATTLE_FRONTPIC_TRANSFER_TILES - 1
	jr .respect_vram_gap
.full_transfer
	ld c, BATTLE_FRONTPIC_TRANSFER_TILES
	jr .respect_vram_gap
.within_transfer_limit
	ld c, a
	cp 1
	jr nz, .respect_vram_gap
	; A one-tile tail is physically padded to two blocks because zero denotes
	; an idle hDMATransfer. Only one logical tile is consumed by the caller.
	inc c

.respect_vram_gap
	ld a, [wBattleFrontpicProducerStagedTiles]
	cp 1
	ret z
	ld a, [wBattleFrontpicProducerVRAMAddress + 1]
	cp HIGH(vTiles5 tile $70)
	ret nz
	ld a, LOW(vTiles5 tile $7f)
	ld hl, wBattleFrontpicProducerVRAMAddress
	sub [hl]
	swap a
	and $f
	ld b, a
	ld a, c
	cp b
	ret c
	ret z
	ld c, b
	ret

.QueueTransfer:
; a = VRAM bank, hl = aligned WRAM0 source, de = VRAM destination,
; c = number of 16-byte blocks (always at least two).
	ld [wBattleFrontpicProducerTransferBank], a
	ldh [rVBK], a
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	and $f0
	ldh [rVDMA_SRC_LOW], a
	ld a, d
	and $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, e
	and $f0
	ldh [rVDMA_DEST_LOW], a
	ld a, c
	dec a
	ldh [hDMATransfer], a
	ret

BattleFrontpicProducer_PrimeBase::
; Wild encounters must have both base copies resident before the first visible
; sliding-intro frame. Dictionary production remains deferred to that slide.
	ld a, [wBattleMode]
	cp WILD_BATTLE
	jr z, .wild
	xor a
	ld [wBattleFrontpicProducerState], a
	ret

.wild
	ldh a, [rVBK]
	push af
.loop
	ld a, [wBattleFrontpicProducerState]
	and a
	jr z, .done
	cp BATTLE_FRONTPIC_PRODUCER_DICTIONARY
	jr nz, .service
	ldh a, [hDMATransfer]
	and a
	jr z, .done
.service
	call BattleFrontpicProducer_Service
	call DelayFrame
	jr .loop
.done
	pop af
	ldh [rVBK], a
	ret

BattleFrontpicProducer_Finish::
; This should normally be a no-op by the time the frontpic animation starts.
; If production fell behind, finish visibly instead of consuming incomplete
; dictionary tiles.
	ldh a, [rVBK]
	push af
.loop
	ld a, [wBattleFrontpicProducerState]
	and a
	jr z, .done
	call BattleFrontpicProducer_Service
	call DelayFrame
	jr .loop
.done
	pop af
	ldh [rVBK], a
	ret

BattleFrontpicProducer_AnimateSlow::
	call BattleFrontpicProducer_Finish
	hlcoord 12, 0
	ld d, 0
	ld e, ANIM_MON_SLOW
	predef AnimateFrontpic
	ret

BattleFrontpicProducer_AnimateNormal::
	call BattleFrontpicProducer_Finish
	hlcoord 12, 0
	ld d, 0
	ld e, ANIM_MON_NORMAL
	predef AnimateFrontpic
	ret

BattleFrontpicProducer_Cancel::
	ld a, [wBattleFrontpicProducerState]
	and a
	ret z
	xor a
	ld [wBattleFrontpicProducerState], a
	ld [wBattleFrontpicProducerStagedTiles], a
	ldh [hDMATransfer], a
	ret

GetFrontpicBaseTileCount:
; a = native square dimension; return its tile count in a.
	ld c, a
	ld b, a
	xor a
.row
	add c
	dec b
	jr nz, .row
	ret

GetPicIndirectPointer:
	ld a, [wCurPartySpecies]
	call GetPokemonIndexFromID
	ld b, h
	ld c, l
	ld a, l
	sub LOW(UNOWN)
	if HIGH(UNOWN) == 0
		or h
	else
		jr nz, .not_unown
		if HIGH(UNOWN) == 1
			dec h
		else
			ld a, h
			cp HIGH(UNOWN)
		endc
	endc
	jr z, .unown
.not_unown
	ld hl, PokemonPicPointers
	ld d, BANK(PokemonPicPointers)
.done
	ld a, 6
	jp AddNTimes

.unown
	ld a, [wUnownLetter]
	ld c, a
	ld b, 0
	ld hl, UnownPicPointers - 6
	ld d, BANK(UnownPicPointers)
	jr .done

GetFrontpicPointer:
	call GetPicIndirectPointer
	ld a, d
	call GetFarByte
	push af
	inc hl
	ld a, d
	call GetFarWord
	pop bc
	ret

GetAnimatedEnemyFrontpic:
	ld a, [wBattleMode]
	and a
	jr z, .skip_battle_menu_dirty
	ld a, [wBattleMenuGFXFlags]
	res BATTLE_MENU_GFX_CLEAN_F, a
	ld [wBattleMenuGFXFlags], a

.skip_battle_menu_dirty
	push hl
	ld de, sPaddedEnemyFrontPic
	ld c, 7 * 7
	ldh a, [hROMBank]
	ld b, a
	call Get2bpp
	pop hl
	ld de, 7 * 7 tiles
	add hl, de
	push hl
	ld a, BANK(wBasePicSize)
	ld hl, wBasePicSize
	call GetFarWRAMByte
	pop hl
	and $f
	ld de, wDecompressScratch + 5 * 5 tiles
	ld c, 5 * 5
	cp 5
	jr z, .got_dims
	ld de, wDecompressScratch + 6 * 6 tiles
	ld c, 6 * 6
	cp 6
	jr z, .got_dims
	ld de, wDecompressScratch + 7 * 7 tiles
	ld c, 7 * 7
.got_dims
	; calculate the number of tiles dedicated to animation
	ld a, [sEnemyFrontPicTileCount]
	sub c
	; exit early if none
	ret z
	ld c, a
	push hl
	push bc
	call LoadFrontpicTiles
	pop bc
	pop hl
	ld de, wDecompressScratch
	ldh a, [hROMBank]
	ld b, a
	; if the tiles fit in a single VRAM block ($80 tiles), load them...
	ld a, c
	sub 128 - 7 * 7
	jr c, .finish
	; otherwise, load as many as we can...
	inc a
	ld [sEnemyFrontPicTileCount], a ; save the remainder
	ld c, 127 - 7 * 7
	call Get2bpp
	; ...and load the rest into vTiles4
	ld de, wDecompressScratch + (127 - 7 * 7) tiles
	ld hl, vTiles4
	ldh a, [hROMBank]
	ld b, a
	ld a, [sEnemyFrontPicTileCount]
	ld c, a
.finish
	jp Get2bpp

LoadFrontpicTiles:
	ld hl, wDecompressScratch
	swap c
	ld a, c
	and $f
	ld b, a
	ld a, c
	and $f0
	ld c, a
	push bc
	call LoadOrientedFrontpic
	pop bc
	ld a, c
	and a
	jr z, .handle_loop
	inc b
	jr .handle_loop

.loop
	push bc
	ld c, 0
	call LoadOrientedFrontpic
	pop bc
.handle_loop
	dec b
	jr nz, .loop
	ret

GetMonBackpic:
	ld a, [wCurPartySpecies]
	call IsAPokemon
	ret c

	ldh a, [rWBK]
	push af
	push de
	call GetPicIndirectPointer
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a

	inc hl
	inc hl
	inc hl
	ld a, d
	call GetFarByte
	push af
	inc hl
	ld a, d
	call GetFarWord
	ld de, wDecompressScratch
	pop af
	call FarDecompress
	ld hl, wDecompressScratch
	ld c, 6 * 6
	call FixBackpicAlignment
	pop hl
	ld de, wDecompressScratch
	ldh a, [hROMBank]
	ld b, a
	call Get2bpp
	pop af
	ldh [rWBK], a
	ret

GetTrainerPic:
	ld a, [wTrainerClass]
	and a
	ret z
	cp NUM_TRAINER_CLASSES + 1
	ret nc
	call WaitBGMap
	xor a
	ldh [hBGMapMode], a
	ld hl, TrainerPicPointers
	ld a, [wTrainerClass]
	dec a
	ld bc, 3
	call AddNTimes
	ldh a, [rWBK]
	push af
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a
	push de
	ld a, BANK(TrainerPicPointers)
	call GetFarByte
	push af
	inc hl
	ld a, BANK(TrainerPicPointers)
	call GetFarWord
	pop af
	ld de, wDecompressScratch
	call FarDecompress
	pop hl
	ld de, wDecompressScratch
	ld c, 7 * 7
	ldh a, [hROMBank]
	ld b, a
	call Get2bpp
	pop af
	ldh [rWBK], a
	call WaitBGMap
	ld a, 1
	ldh [hBGMapMode], a
	ret

DecompressGet2bpp:
; Decompress lz data from b:hl to wDecompressScratch, then copy it to address de.

	ldh a, [rWBK]
	push af
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a

	push de
	push bc
	ld a, b
	ld de, wDecompressScratch
	call FarDecompress
	pop bc
	ld de, wDecompressScratch
	pop hl
	ldh a, [hROMBank]
	ld b, a
	call Get2bpp

	pop af
	ldh [rWBK], a
	ret

FixBackpicAlignment:
	push de
	push bc
	ld a, [wBoxAlignment]
	and a
	jr z, .keep_dims
	ld a, c
	cp 7 * 7
	ld de, 7 * 7 tiles
	jr z, .got_dims
	cp 6 * 6
	ld de, 6 * 6 tiles
	jr z, .got_dims
	ld de, 5 * 5 tiles

.got_dims
	ld a, [hl]
	ld b, 0
	ld c, 8
.loop
	rra
	rl b
	dec c
	jr nz, .loop
	ld a, b
	ld [hli], a
	dec de
	ld a, e
	or d
	jr nz, .got_dims

.keep_dims
	pop bc
	pop de
	ret

PadFrontpic:
; pads frontpic to fill 7x7 box
	ld a, b
	cp 6
	jr z, .six
	cp 5
	jr z, .five

.seven_loop
	ld c, 7 << 4
	call LoadOrientedFrontpic
	dec b
	jr nz, .seven_loop
	ret

.six
	ld c, 7 << 4
	xor a
	call .Fill
.six_loop
	ld c, (7 - 6) << 4
	xor a
	call .Fill
	ld c, 6 << 4
	call LoadOrientedFrontpic
	dec b
	jr nz, .six_loop
	ret

.five
	ld c, 7 << 4
	xor a
	call .Fill
.five_loop
	ld c, (7 - 5) << 4
	xor a
	call .Fill
	ld c, 5 << 4
	call LoadOrientedFrontpic
	dec b
	jr nz, .five_loop
	ld c, 7 << 4
	xor a
	call .Fill
	ret

.Fill:
	ld [hli], a
	dec c
	jr nz, .Fill
	ret

LoadOrientedFrontpic:
	ld a, [wBoxAlignment]
	and a
	jr nz, .x_flip
.left_loop
	ld a, [de]
	inc de
	ld [hli], a
	dec c
	jr nz, .left_loop
	ret

.x_flip
	push bc
.right_loop
	ld a, [de]
	inc de
	ld b, a
	xor a
rept 8
	rr b
	rla
endr
	ld [hli], a
	dec c
	jr nz, .right_loop
	pop bc
	ret
