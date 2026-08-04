ASSERT POKEDEX_ANIM_SLOT_A_MAP + 7 * 7 == POKEDEX_ANIM_SLOT_A_ATTRS
ASSERT POKEDEX_ANIM_SLOT_B_MAP + 7 * 7 == POKEDEX_ANIM_SLOT_B_ATTRS
ASSERT POKEDEX_ANIM_SOURCE_TILES + 7 * 7 <= wPokedexWRAM0ScratchEnd

Pokedex_UpdateScrolledGrid:
; Preserve the visible Listing while the next selection and grid are staged.
; The final grid map, palette, and OAM state is revealed as one transaction.
	call Pokedex_CancelAnimationPrefetch
	ld a, TRUE
	ldh [hOAMUpdate], a
	xor a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	ld [wPokedexGridScrollFlags], a

	; FarCall preserves flags but not a. Rebuild the returned render key from
	; the preserved seen result and wTempSpecies before comparing or staging it.
	farcall Pokedex_GetSelectionRenderKey
	ld a, POKEDEX_RENDER_KEY_UNSEEN
	jr z, .got_selection_key
	ld a, [wTempSpecies]
.got_selection_key
	ld [wCurPartySpecies], a
	ld hl, wPokedexRenderedSelectionKey
	cp [hl]
	jr z, .selection_key_ready
	ld hl, wPokedexGridScrollFlags
	set POKEDEX_GRID_SCROLL_SELECTION_F, [hl]
.selection_key_ready
	ld a, [wPokedexGridScrollFlags]
	bit POKEDEX_GRID_SCROLL_SELECTION_F, a
	jr z, .selection_prepared
	farcall Pokedex_PrintSelectedName
	farcall Pokedex_PrepareSelectedMonTiles
.selection_prepared
	ld a, [wPokedexGridScrollFlags]
	bit POKEDEX_GRID_SCROLL_SELECTION_F, a
	jr z, .selection_committed
	farcall Pokedex_CommitStagedSelection
.selection_committed
	farcall Pokedex_SyncGridIconAnimationFrame
	farcall Pokedex_DrawListGrid
	farcall CGB_PokedexStageListPalettes
	farcall Pokedex_UpdateGridOAM
	call Pokedex_CommitScrolledGridReveal
	farcall Pokedex_RecordRenderedSelectionKey

	; The incoming row was already resident. Refill the newly offscreen cache
	; row only after the complete visible state has been revealed.
	farcall Pokedex_PrepareGridCacheRefill
	farcall Pokedex_UploadPendingGridCacheRow
	call Pokedex_StartAnimationPrefetch
	ret

Pokedex_CommitScrolledGridReveal:
; Rows 5-14 contain the nine 2x2 grid cells. Wait until their final visible
; scanline has passed, then replace only their tilemap and attributes. The
; selection-dependent palettes are committed in the same transaction, and
; the prepared shadow OAM is released for the following VBlank.
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .lcd_off

.wait_grid_end
	ldh a, [rLY]
	cp 144
	jr nc, .wait_next_frame
	cp 120
	jr c, .wait_grid_end
	jr .reveal

.wait_next_frame
	ldh a, [rLY]
	cp 144
	jr nc, .wait_next_frame
	jr .wait_grid_end

.reveal
	di
	call Pokedex_CopyScrolledGridToVRAM
	call Pokedex_CommitScrolledGridPalettes
	xor a
	ldh [hOAMUpdate], a
	ei
	call DelayFrame
	ret

.lcd_off
	call Pokedex_CopyScrolledGridToVRAM
	xor a
	ldh [hOAMUpdate], a
	ret

Pokedex_CopyScrolledGridToVRAM:
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld hl, .TilemapCells
	call .CopyCells
	ld a, BANK(vTiles3)
	ldh [rVBK], a
	ld hl, .AttrmapCells
	call .CopyCells
	pop af
	ldh [rVBK], a
	ret

.CopyCells:
	ld a, POKEDEX_GRID_SIZE
.next_cell
	push af
	ld c, [hl]
	inc hl
	ld b, [hl]
	inc hl
	ld e, [hl]
	inc hl
	ld d, [hl]
	inc hl
	push hl
	ld h, b
	ld l, c
	call .CopyCell
	pop hl
	pop af
	dec a
	jr nz, .next_cell
	ret

.CopyCell:
	ld c, 2
.next_row
	ld b, 2
.next_tile
.wait_vram
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_vram
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .next_tile
	dec c
	ret z
	ld a, l
	add SCREEN_WIDTH - 2
	ld l, a
	jr nc, .source_ready
	inc h
.source_ready
	ld a, e
	add TILEMAP_WIDTH - 2
	ld e, a
	jr nc, .dest_ready
	inc d
.dest_ready
	jr .next_row

.TilemapCells:
	dw wTilemap +  5 * SCREEN_WIDTH + 1, vBGMap1 +  5 * TILEMAP_WIDTH + 1
	dw wTilemap +  5 * SCREEN_WIDTH + 5, vBGMap1 +  5 * TILEMAP_WIDTH + 5
	dw wTilemap +  5 * SCREEN_WIDTH + 9, vBGMap1 +  5 * TILEMAP_WIDTH + 9
	dw wTilemap +  9 * SCREEN_WIDTH + 1, vBGMap1 +  9 * TILEMAP_WIDTH + 1
	dw wTilemap +  9 * SCREEN_WIDTH + 5, vBGMap1 +  9 * TILEMAP_WIDTH + 5
	dw wTilemap +  9 * SCREEN_WIDTH + 9, vBGMap1 +  9 * TILEMAP_WIDTH + 9
	dw wTilemap + 13 * SCREEN_WIDTH + 1, vBGMap1 + 13 * TILEMAP_WIDTH + 1
	dw wTilemap + 13 * SCREEN_WIDTH + 5, vBGMap1 + 13 * TILEMAP_WIDTH + 5
	dw wTilemap + 13 * SCREEN_WIDTH + 9, vBGMap1 + 13 * TILEMAP_WIDTH + 9

.AttrmapCells:
	dw wAttrmap +  5 * SCREEN_WIDTH + 1, vBGMap1 +  5 * TILEMAP_WIDTH + 1
	dw wAttrmap +  5 * SCREEN_WIDTH + 5, vBGMap1 +  5 * TILEMAP_WIDTH + 5
	dw wAttrmap +  5 * SCREEN_WIDTH + 9, vBGMap1 +  5 * TILEMAP_WIDTH + 9
	dw wAttrmap +  9 * SCREEN_WIDTH + 1, vBGMap1 +  9 * TILEMAP_WIDTH + 1
	dw wAttrmap +  9 * SCREEN_WIDTH + 5, vBGMap1 +  9 * TILEMAP_WIDTH + 5
	dw wAttrmap +  9 * SCREEN_WIDTH + 9, vBGMap1 +  9 * TILEMAP_WIDTH + 9
	dw wAttrmap + 13 * SCREEN_WIDTH + 1, vBGMap1 + 13 * TILEMAP_WIDTH + 1
	dw wAttrmap + 13 * SCREEN_WIDTH + 5, vBGMap1 + 13 * TILEMAP_WIDTH + 5
	dw wAttrmap + 13 * SCREEN_WIDTH + 9, vBGMap1 + 13 * TILEMAP_WIDTH + 9

Pokedex_CommitScrolledGridPalettes:
	ldh a, [hCGB]
	and a
	ret z
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals2)
	ldh [rWBK], a

	ld hl, wBGPals2 palette 1
	ld a, BGPI_AUTOINC palette 1
	ldh [rBGPI], a
	ld c, LOW(rBGPD)
	ld b, 7 palettes
	call .CopyBytes

	ld hl, wOBPals2 palette 2
	ld a, OBPI_AUTOINC palette 2
	ldh [rOBPI], a
	ld c, LOW(rOBPD)
	ld b, 3 palettes
	call .CopyBytes

	pop af
	ldh [rWBK], a
	ret

.CopyBytes:
.wait_palette
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_palette
	ld a, [hli]
	ldh [c], a
	dec b
	jr nz, .CopyBytes
	ret

Pokedex_CancelAnimationPrefetch:
	xor a
	ld [wPokedexAnimProducerState], a
	ld [wPokedexAnimPlaybackState], a
	ld hl, wPokedexAnimSlotStates
	ld bc, 2
	call ByteFill
	ld a, -1
	ld [wPokedexAnimDisplaySlot], a
	ret

Pokedex_StartAnimationPrefetch:
; The static frontpic loader has already left this species' complete tile
; dictionary in WRAMX6. Starting a job only updates state; decoding remains an
; idle-frame operation so selection changes do not gain any extra latency.
	call Pokedex_CancelAnimationPrefetch
	ldh a, [hCGB]
	and a
	ret z
	farcall Pokedex_GetSelectedMon
	farcall Pokedex_CheckSeen
	ret z
	ld a, [wTempSpecies]
	ld [wPokedexAnimOwner], a
	ld [wCurPartySpecies], a
	xor a
	ld [wBoxAlignment], a
	ld [wPokedexAnimProduceSlot], a
	ld [wPokedexAnimConsumeSlot], a
	ld [wPokedexAnimProducerPhase], a
	ld [wPokedexAnimTrailingHold], a
	ld hl, wPokedexAnimSlotStates
	ld bc, 8
	call ByteFill
	ld a, POKEDEX_ANIM_PRODUCER_PENDING
	ld [wPokedexAnimProducerState], a
	ret

Pokedex_BeginDescriptionAnimation:
	ldh a, [hCGB]
	and a
	ret z
	farcall Pokedex_GetSelectedMon
	farcall Pokedex_CheckSeen
	ret z
	ld a, [wTempSpecies]
	ld [wCurPartySpecies], a
	ld hl, wPokedexAnimOwner
	cp [hl]
	jr nz, .restart
	ld a, [wPokedexAnimProducerState]
	and a
	jr z, .restart
	cp POKEDEX_ANIM_PRODUCER_PENDING
	jr z, .begin
	ld a, [wPrevDexEntryJumptableIndex]
	cp DEXSTATE_MAIN_SCR
	jr z, .begin
.restart
	call Pokedex_StartAnimationPrefetch
.begin
	ld a, POKEDEX_ANIM_PLAYBACK_WAITING
	ld [wPokedexAnimPlaybackState], a
	ret

Pokedex_ServiceAnimationProducer:
	ldh a, [hCGB]
	and a
	ret z
	ld a, [wPokedexAnimProducerState]
	cp POKEDEX_ANIM_PRODUCER_PENDING
	jr z, .initialize
	cp POKEDEX_ANIM_PRODUCER_ACTIVE
	ret nz
	jr .produce

.initialize
	ld de, POKEDEX_ANIM_LOGICAL_MAP
	ld b, 0
	ld a, [wPokedexAnimProducerPhase]
	ld c, a
	farcall PokeAnim_InitFrameProducer
	ld [wPokedexAnimFrontpicDim], a
	ld a, POKEDEX_ANIM_PRODUCER_ACTIVE
	ld [wPokedexAnimProducerState], a

.produce
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotState
	ld a, [hl]
	cp POKEDEX_ANIM_SLOT_BUILDING
	jp z, Pokedex_TryUploadAnimationSlot
	cp POKEDEX_ANIM_SLOT_EMPTY
	ret nz

	farcall PokeAnim_DecodeNextVisualFrame
	jr nc, .ended
	ld [wDexTempCounter], a
	ld a, b
	ld [wDexTempCounter + 1], a
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotDuration
	ld a, [wDexTempCounter]
	ld [hl], a
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotPrehold
	ld a, [wDexTempCounter + 1]
	ld [hl], a
	jp Pokedex_BuildAnimationSlot

.ended
	ld a, b
	ld [wPokedexAnimTrailingHold], a
	ld a, POKEDEX_ANIM_PRODUCER_ENDED
	ld [wPokedexAnimProducerState], a
	ret

Pokedex_BuildAnimationSlot:
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotTileCount
	xor a
	ld [hl], a

	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotMap
	ld d, h
	ld e, l
	ld hl, POKEDEX_ANIM_LOGICAL_MAP
	ld b, 7
.map_row
	ld c, 7
.map_col
	push bc
	ld a, [hli]
	call Pokedex_NormalizeAnimationTile
	jr nc, .base_tile

	push hl
	push de
	push af
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotTileCount
	ld c, [hl]
	inc [hl]
	pop af
	ld b, a
	ld hl, POKEDEX_ANIM_SOURCE_TILES
	ld e, c
	ld d, 0
	add hl, de
	ld [hl], b
	pop de
	ld a, [wPokedexAnimProduceSlot]
	and a
	ld a, POKEDEX_ANIM_BUFFER_A_TILE
	jr z, .got_buffer_tile
	ld a, POKEDEX_ANIM_BUFFER_B_TILE
.got_buffer_tile
	add c
	ld [de], a
	inc de
	pop hl
	jr .next_map_tile

.base_tile
	ld [de], a
	inc de
.next_map_tile
	pop bc
	dec c
	jr nz, .map_col
	push bc
	ld bc, SCREEN_WIDTH - 7
	add hl, bc
	pop bc
	dec b
	jr nz, .map_row

	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotMap
	ld d, h
	ld e, l
	ld bc, 7 * 7
	add hl, bc
	ld a, [wPokedexAnimProduceSlot]
	and a
	ld b, POKEDEX_ANIM_BUFFER_A_TILE
	jr z, .got_attr_buffer_tile
	ld b, POKEDEX_ANIM_BUFFER_B_TILE
.got_attr_buffer_tile
	ld c, 7 * 7
.attr_loop
	ld a, [de]
	inc de
	cp b
	ld a, 1
	jr c, .store_attr
	or BG_BANK1
.store_attr
	ld [hli], a
	dec c
	jr nz, .attr_loop

	call Pokedex_GatherAnimationTiles
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotState
	ld [hl], POKEDEX_ANIM_SLOT_BUILDING
	jp Pokedex_TryUploadAnimationSlot

Pokedex_NormalizeAnimationTile:
; Convert the parser's padded tile number back to the raw WRAMX6 dictionary
; index. Carry is set only for tiles that must be streamed into bank 1.
	cp $80
	jr c, .no_skipped_tile
	dec a
.no_skipped_tile
	cp 7 * 7
	jr nc, .animation_tile
	and a
	ret
.animation_tile
	push af
	ld a, [wPokedexAnimFrontpicDim]
	cp 5
	jr z, .five_by_five
	cp 6
	jr z, .six_by_six
	pop af
	scf
	ret
.five_by_five
	pop af
	sub 7 * 7 - 5 * 5
	scf
	ret
.six_by_six
	pop af
	sub 7 * 7 - 6 * 6
	scf
	ret

Pokedex_GatherAnimationTiles:
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotTileCount
	ld c, [hl]
	ld a, c
	and a
	ret z
	ldh a, [rWBK]
	push af
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a
	ld hl, POKEDEX_ANIM_SOURCE_TILES
	ld de, POKEDEX_ANIM_PAYLOAD
.tile_loop
	push bc
	ld a, [hli]
	push hl
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld bc, wDecompressScratch
	add hl, bc
	ld b, TILE_SIZE
.byte_loop
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .byte_loop
	pop hl
	pop bc
	dec c
	jr nz, .tile_loop
	pop af
	ldh [rWBK], a
	ret

Pokedex_TryUploadAnimationSlot:
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotTileCount
	ld c, [hl]
	ld a, c
	and a
	jr z, .uploaded

	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .copy_lcd_off
	ld b, c
	ld a, $80
	sub b
	ld b, a
	ldh a, [rLY]
	cp b
	ret nc

	xor a
	ldh [hBGMapMode], a
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotVRAM
	ld hl, POKEDEX_ANIM_PAYLOAD
	call Pokedex_HDMATransferAnimationGFX
	pop af
	ldh [rVBK], a
	jr .uploaded

.copy_lcd_off
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	ld a, [wPokedexAnimProduceSlot]
	call Pokedex_GetAnimationSlotVRAM
	ld hl, POKEDEX_ANIM_PAYLOAD
	ld b, 0
	ld a, c
	swap a
	ld c, a
	and $f
	ld b, a
	ld a, c
	and $f0
	ld c, a
	call CopyBytes
	pop af
	ldh [rVBK], a

.uploaded
	ld a, [wPokedexAnimProduceSlot]
	ld b, a
	ld a, [wPokedexAnimDisplaySlot]
	cp b
	ld c, POKEDEX_ANIM_SLOT_DISPLAYED
	jr z, .set_slot_state
	ld c, POKEDEX_ANIM_SLOT_READY
.set_slot_state
	ld a, b
	call Pokedex_GetAnimationSlotState
	ld [hl], c
	ld a, b
	xor 1
	ld [wPokedexAnimProduceSlot], a
	ret

Pokedex_UpdateDescriptionAnimation:
	ldh a, [hCGB]
	and a
	ret z
	ld a, [wPokedexAnimPlaybackState]
	cp POKEDEX_ANIM_PLAYBACK_WAITING
	jr z, .waiting
	cp POKEDEX_ANIM_PLAYBACK_PLAYING
	jr z, .playing
	cp POKEDEX_ANIM_PLAYBACK_MAIN_HOLD
	jr z, .holding
	cp POKEDEX_ANIM_PLAYBACK_PREHOLD
	jr z, .holding
	ret

.waiting
	xor a
	call Pokedex_GetAnimationSlotState
	ld a, [hl]
	cp POKEDEX_ANIM_SLOT_READY
	ret nz
	ld a, 1
	call Pokedex_GetAnimationSlotState
	ld a, [hl]
	cp POKEDEX_ANIM_SLOT_READY
	jr z, .start
	ld a, [wPokedexAnimProducerState]
	cp POKEDEX_ANIM_PRODUCER_ENDED
	ret nz
.start
	ld a, [wPokedexAnimOwner]
	call PlayMonCry2
	ld a, POKEDEX_ANIM_PLAYBACK_PLAYING
	ld [wPokedexAnimPlaybackState], a
	xor a
	jp Pokedex_InstallAnimationSlot

.playing
	ld hl, wPokedexAnimPlaybackTimer
	dec [hl]
	ret nz
	jp Pokedex_AdvanceDescriptionAnimation

.holding
	ld hl, wPokedexAnimHoldTimer
	dec [hl]
	ret nz
	ld a, POKEDEX_ANIM_PLAYBACK_PLAYING
	ld [wPokedexAnimPlaybackState], a
	jp Pokedex_AdvanceDescriptionAnimation

Pokedex_AdvanceDescriptionAnimation:
	ld a, [wPokedexAnimConsumeSlot]
	call Pokedex_GetAnimationSlotPrehold
	ld a, [hl]
	and a
	jr z, .check_slot
	ld [wPokedexAnimHoldTimer], a
	xor a
	ld [hl], a
	ld a, POKEDEX_ANIM_PLAYBACK_PREHOLD
	ld [wPokedexAnimPlaybackState], a
	ret

.check_slot
	ld a, [wPokedexAnimConsumeSlot]
	call Pokedex_GetAnimationSlotState
	ld a, [hl]
	cp POKEDEX_ANIM_SLOT_READY
	jr z, .install
	cp POKEDEX_ANIM_SLOT_BUILDING
	jr z, .underrun_install
	ld a, [wPokedexAnimProducerState]
	cp POKEDEX_ANIM_PRODUCER_ENDED
	jr nz, .underrun_empty
	ld a, [wPokedexAnimTrailingHold]
	and a
	jr z, .check_phase_end
	ld [wPokedexAnimHoldTimer], a
	xor a
	ld [wPokedexAnimTrailingHold], a
	ld a, POKEDEX_ANIM_PLAYBACK_PREHOLD
	ld [wPokedexAnimPlaybackState], a
	ret

.check_phase_end
	ld a, [wPokedexAnimProducerPhase]
	cp POKEDEX_ANIM_PHASE_MAIN
	jr nz, .finished

.begin_main_hold
	call Pokedex_RestoreBaseFrontpicMap
	ld a, POKEDEX_ANIM_PHASE_IDLE
	ld [wPokedexAnimProducerPhase], a
	ld a, POKEDEX_ANIM_PRODUCER_PENDING
	ld [wPokedexAnimProducerState], a
	xor a
	ld [wPokedexAnimProduceSlot], a
	ld [wPokedexAnimConsumeSlot], a
	ld a, 18
	ld [wPokedexAnimHoldTimer], a
	ld a, POKEDEX_ANIM_PLAYBACK_MAIN_HOLD
	ld [wPokedexAnimPlaybackState], a
	ret

.finished
	call Pokedex_RestoreBaseFrontpicMap
	ld a, POKEDEX_ANIM_PLAYBACK_DONE
	ld [wPokedexAnimPlaybackState], a
	xor a
	ld [wPokedexAnimProducerState], a
	ret

.underrun_install
	call Pokedex_CountAnimationUnderflow
.install
	ld a, [wPokedexAnimConsumeSlot]
	jp Pokedex_InstallAnimationSlot

.underrun_empty
	call Pokedex_CountAnimationUnderflow
	call Pokedex_BuildAnimationUnderflowMap
	ld a, [wPokedexAnimConsumeSlot]
	call Pokedex_InstallAnimationSlot
	ld a, [wPokedexAnimConsumeSlot]
	ld [wPokedexAnimProduceSlot], a
	ret

Pokedex_CountAnimationUnderflow:
	ld hl, wPokedexAnimUnderflowCount
	inc [hl]
	ret nz
	inc hl
	inc [hl]
	ret

Pokedex_BuildAnimationUnderflowMap:
; With no decoded frame at all, expose every tile in the expected buffer.
; This deliberately displays stale/incomplete graphics instead of hiding an
; underrun behind the previous complete frame.
	ld a, [wPokedexAnimConsumeSlot]
	call Pokedex_GetAnimationSlotMap
	ld d, h
	ld e, l
	ld a, [wPokedexAnimConsumeSlot]
	and a
	ld a, POKEDEX_ANIM_BUFFER_A_TILE
	jr z, .got_tile
	ld a, POKEDEX_ANIM_BUFFER_B_TILE
.got_tile
	ld c, 7 * 7
.map_loop
	ld [de], a
	inc de
	inc a
	dec c
	jr nz, .map_loop
	ld a, [wPokedexAnimConsumeSlot]
	call Pokedex_GetAnimationSlotMap
	ld bc, 7 * 7
	add hl, bc
	ld a, 1 | BG_BANK1
	call ByteFill
	ld a, [wPokedexAnimConsumeSlot]
	call Pokedex_GetAnimationSlotDuration
	ld [hl], 1
	ld a, [wPokedexAnimConsumeSlot]
	call Pokedex_GetAnimationSlotState
	ld [hl], POKEDEX_ANIM_SLOT_READY
	ret

Pokedex_InstallAnimationSlot:
; a = slot. Install the packed tile/attribute maps, then release the buffer
; that was visible previously.
	push af
	call Pokedex_GetAnimationSlotMap
	ld d, h
	ld e, l
	farcall Pokedex_CommitAnimationFrontpicMap
	pop af
	ld b, a
	ld a, [wPokedexAnimDisplaySlot]
	cp -1
	jr z, .set_new
	cp b
	jr z, .set_new
	call Pokedex_GetAnimationSlotState
	ld [hl], POKEDEX_ANIM_SLOT_EMPTY
.set_new
	ld a, b
	ld [wPokedexAnimDisplaySlot], a
	call Pokedex_GetAnimationSlotState
	ld a, [hl]
	cp POKEDEX_ANIM_SLOT_BUILDING
	jr z, .set_timer
	ld [hl], POKEDEX_ANIM_SLOT_DISPLAYED
.set_timer
	ld a, b
	call Pokedex_GetAnimationSlotDuration
	ld a, [hl]
	ld [wPokedexAnimPlaybackTimer], a
	ld a, b
	xor 1
	ld [wPokedexAnimConsumeSlot], a
	ret

Pokedex_RestoreBaseFrontpicMap:
	farcall Pokedex_PlaceFrontpicTopLeftCorner
	hlcoord 1, 1, wAttrmap
	ld b, 7
.attr_row
	ld c, 7
.attr_col
	ld [hl], 1
	inc hl
	dec c
	jr nz, .attr_col
	ld de, SCREEN_WIDTH - 7
	add hl, de
	dec b
	jr nz, .attr_row
	farcall Pokedex_CommitCurrentFrontpicMap
	ld hl, wPokedexAnimSlotStates
	ld bc, 2
	xor a
	call ByteFill
	ld a, -1
	ld [wPokedexAnimDisplaySlot], a
	ret

Pokedex_StopDescriptionAnimation:
	ldh a, [hCGB]
	and a
	jp z, Pokedex_CancelAnimationPrefetch
	ld a, [wPokedexAnimDisplaySlot]
	cp -1
	call nz, Pokedex_RestoreBaseFrontpicMap
	jp Pokedex_CancelAnimationPrefetch

Pokedex_GetAnimationSlotState:
	ld hl, wPokedexAnimSlotStates
	jr Pokedex_AddSlotOffset

Pokedex_GetAnimationSlotDuration:
	ld hl, wPokedexAnimSlotDurations
	jr Pokedex_AddSlotOffset

Pokedex_GetAnimationSlotPrehold:
	ld hl, wPokedexAnimSlotPreholds
	jr Pokedex_AddSlotOffset

Pokedex_GetAnimationSlotTileCount:
	ld hl, wPokedexAnimSlotTileCounts
Pokedex_AddSlotOffset:
	ld e, a
	ld d, 0
	add hl, de
	ret

Pokedex_GetAnimationSlotMap:
	and a
	ld hl, POKEDEX_ANIM_SLOT_A_MAP
	ret z
	ld hl, POKEDEX_ANIM_SLOT_B_MAP
	ret

Pokedex_GetAnimationSlotVRAM:
	and a
	ld de, vTiles4
	ret z
	ld de, vTiles5 tile POKEDEX_ANIM_BUFFER_B_TILE
	ret

Pokedex_LoadPermanentCGBGFX:
	ldh a, [hCGB]
	and a
	ret z
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	ld de, PokedexListJoinedLeftGFX
	ld hl, vTiles4 tile $50
	lb bc, BANK(PokedexListJoinedLeftGFX), 1
	call Get2bpp
	ld de, PokedexListJoinedMiddleGFX
	ld hl, vTiles4 tile $51
	lb bc, BANK(PokedexListJoinedMiddleGFX), 1
	call Get2bpp
	ld de, vTiles5 tile $32
	farcall Pokedex_MakeTileDarkGrayAtDE
	pop af
	ldh [rVBK], a
	farcall Pokedex_LoadUnownFont
	ret
