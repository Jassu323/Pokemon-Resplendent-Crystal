ASSERT POKEDEX_ANIM_SLOT_A_MAP + 7 * 7 == POKEDEX_ANIM_SLOT_A_ATTRS
ASSERT POKEDEX_ANIM_SLOT_B_MAP + 7 * 7 == POKEDEX_ANIM_SLOT_B_ATTRS
ASSERT POKEDEX_ANIM_SOURCE_TILES + 7 * 7 <= wPokedexWRAM0ScratchEnd

DEF POKEDEX_WRAP_MAP_STAGING EQUS "POKEDEX_GRID_CENTER_GFX"
DEF POKEDEX_WRAP_MAP_BLOCKS EQU 13
ASSERT LOW(POKEDEX_WRAP_MAP_STAGING) & $f == 0
ASSERT POKEDEX_WRAP_MAP_STAGING + POKEDEX_WRAP_MAP_BLOCKS * $10 <= wPokedexWRAM0ScratchEnd

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
	; Finish every WRAM and shadow-state update before streaming the selection.
	; The grid reveal can then follow the frontpic transfer in the same frame.
	farcall Pokedex_SyncGridIconAnimationFrame
	farcall Pokedex_DrawListGrid
	farcall CGB_PokedexStageListPalettes
	farcall Pokedex_UpdateGridOAM
	ld a, [wPokedexGridScrollFlags]
	bit POKEDEX_GRID_SCROLL_SELECTION_F, a
	jr z, .selection_committed
	farcall Pokedex_CommitStagedSelection
.selection_committed
	call Pokedex_CommitScrolledGridReveal
	farcall Pokedex_RecordRenderedSelectionKey

	; The incoming row was already resident. Refill the newly offscreen cache
	; row only after the complete visible state has been revealed.
	farcall Pokedex_PrepareGridCacheRefill
	farcall Pokedex_UploadPendingGridCacheRow
	call Pokedex_StartAnimationPrefetch
	ret

Pokedex_UpdateWrappedGrid:
; A wrap replaces all three visible rows. Build the destination in the two
; offscreen cache rows plus the expired old top row, then reveal one complete
; grid without disabling the LCD or reserving another icon cache.
	call Pokedex_CancelAnimationPrefetch
	ld a, TRUE
	ldh [hOAMUpdate], a
	xor a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	ld [wPokedexGridScrollFlags], a

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

	; The first two rows go to offscreen physical slots. The third remains in
	; WRAM staging until its old on-screen pixels have passed.
	farcall Pokedex_PrepareWrappedGridRows
	farcall Pokedex_LoadGridPage
	farcall Pokedex_SyncGridIconAnimationFrame
	farcall Pokedex_DrawListGrid
	farcall CGB_PokedexStageListPalettes
	farcall Pokedex_UpdateGridOAM
	farcall Pokedex_UploadWrappedBottomRow
	call Pokedex_CommitWrappedGridReveal
	farcall Pokedex_RecordRenderedSelectionKey
	ld a, [wPokedexGridScrollFlags]
	bit POKEDEX_GRID_SCROLL_SELECTION_F, a
	jr z, .footprint_ready
	ld a, [wCurPartySpecies]
	cp POKEDEX_RENDER_KEY_UNSEEN
	jr z, .footprint_ready
	farcall Pokedex_TransferPreparedFootprint
	ld a, [wCurPartySpecies]
	ld [wPokedexResidentFootprintSpecies], a
.footprint_ready

	; Rebuild the one useful neighbor row. The opposite endpoint row is marked
	; invalid so later cache validation cannot mistake stale ownership for data.
	farcall Pokedex_FinalizeWrappedGridCache
	xor a
	ld [wPokedexGridScrollDirection], a
	call Pokedex_StartAnimationPrefetch
	ret

Pokedex_CommitWrappedGridReveal:
; Replace each target row only after the corresponding outgoing pixels have
; passed. VBlank then owns the portrait, hardware palettes, and shadow OAM as
; one indivisible reveal transaction.
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .lcd_off
	; All three target icon rows are resident now, so their former staging area
	; can hold aligned map blocks without consuming additional WRAM.
	call Pokedex_StageWrappedGridMapBlocks

	; The bottom cache upload normally returns after scanline 80. If it ever
	; finishes in VBlank, leave the old frame complete and begin next frame.
.wait_top_end
	ldh a, [rLY]
	cp 144
	jr nc, .wait_next_frame
	cp 56
	jr c, .wait_top_end

	ld a, [wPokedexGridScrollFlags]
	bit POKEDEX_GRID_SCROLL_SELECTION_F, a
	jr z, .copy_top_row
	call Pokedex_TransferWrappedSelectionName
.copy_top_row
	call Pokedex_TransferWrappedGridTopRow

.wait_middle_end
	ldh a, [rLY]
	cp 88
	jr c, .wait_middle_end
	call Pokedex_TransferWrappedGridMiddleRow

.wait_bottom_end
	ldh a, [rLY]
	cp 120
	jr c, .wait_bottom_end
	call Pokedex_TransferWrappedGridBottomRow
	ld hl, wPokedexGridScrollFlags
	set POKEDEX_GRID_SCROLL_COMMIT_F, [hl]
	call DelayFrame
	; The Pokédex VBlank handler transferred OAM itself and left the normal
	; handler locked out for that frame. Return ownership to normal VBlanks.
	xor a
	ldh [hOAMUpdate], a
	ret

.wait_next_frame
	ldh a, [rLY]
	cp 144
	jr nc, .wait_next_frame
	jr .wait_top_end

.lcd_off
	ld a, [wPokedexGridScrollFlags]
	bit POKEDEX_GRID_SCROLL_SELECTION_F, a
	jr z, .copy_grid_lcd_off
	farcall Pokedex_CommitWrappedSelectionGFX
	farcall Pokedex_CommitStagedSelectionName
.copy_grid_lcd_off
	call Pokedex_CopyScrolledGridToVRAM
	call Pokedex_CommitScrolledGridPalettes
	xor a
	ldh [hOAMUpdate], a
	ret

Pokedex_WrapGridToTop:
; Keep the cursor in its current column and replace the complete bottom
; viewport with the complete first viewport.
	ld a, b
.get_column
	cp POKEDEX_GRID_WIDTH
	jr c, .got_column
	sub POKEDEX_GRID_WIDTH
	jr .get_column
.got_column
	ld c, a
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld e, b
	ld d, 0
	add hl, de
	ld a, h
	or a
	jr nz, .move
	ld a, l
	cp c
	jr z, .no_move
.move
	ld hl, wDexListingScrollOffset
	ld a, [hli]
	or [hl]
	jr z, .move_within_view
	ld a, TRUE
	ldh [hOAMUpdate], a
	xor a
	ld [wDexListingScrollOffset], a
	ld [wDexListingScrollOffset + 1], a
	ld a, c
	ld [wDexListingCursor], a
	ld a, POKEDEX_GRID_SCROLL_WRAP_DOWN
	ld [wPokedexGridScrollDirection], a
	scf
	ret
.move_within_view
	ld a, c
	ld [wDexListingCursor], a
	scf
	ret
.no_move
	and a
	ret

Pokedex_WrapGridToBottom:
; Find the final valid entry in the current column, then place it in the
; complete final three-row viewport. The list can exceed one byte.
	ld a, b
.get_column
	cp POKEDEX_GRID_WIDTH
	jr c, .got_column
	sub POKEDEX_GRID_WIDTH
	jr .get_column
.got_column
	ld l, a
	ld h, 0
.find_final_entry
	push hl
	ld de, POKEDEX_GRID_WIDTH
	add hl, de
	call Pokedex_GridOffsetBeforeListingEnd
	jr nc, .found_final_entry
	pop de
	jr .find_final_entry
.found_final_entry
	pop hl
	ld a, h
	or a
	jr nz, .save_final_entry
	ld a, l
	cp POKEDEX_GRID_WIDTH
	jr c, .no_move
.save_final_entry
	ld a, l
	ld [wDexTempCounter], a
	ld a, h
	ld [wDexTempCounter + 1], a

	; Advance an aligned viewport while a complete successor position still
	; exists. This yields max(0, ceil(list_length / 3) - 3) * 3.
	ld bc, 0
.find_final_viewport
	ld h, b
	ld l, c
	ld de, POKEDEX_GRID_SIZE
	add hl, de
	call Pokedex_GridOffsetBeforeListingEnd
	jr nc, .got_final_viewport
	inc bc
	inc bc
	inc bc
	jr .find_final_viewport
.got_final_viewport
	ld a, b
	or c
	jr z, .store_final_viewport
	ld a, TRUE
	ldh [hOAMUpdate], a
.store_final_viewport
	ld a, c
	ld [wDexListingScrollOffset], a
	ld a, b
	ld [wDexListingScrollOffset + 1], a
	ld a, [wDexTempCounter]
	sub c
	ld e, a
	ld a, [wDexTempCounter + 1]
	sbc b
	ld a, e
	ld [wDexListingCursor], a
	ld a, b
	or c
	jr z, .moved_within_view
	ld a, POKEDEX_GRID_SCROLL_WRAP_UP
	ld [wPokedexGridScrollDirection], a
	scf
	ret
.moved_within_view
	scf
	ret
.no_move
	and a
	ret

Pokedex_GridOffsetBeforeListingEnd:
; Return carry when hl is a valid absolute Listing offset. Preserve hl/bc.
	ld a, [wDexListingEnd]
	ld e, a
	ld a, [wDexListingEnd + 1]
	ld d, a
	ld a, h
	cp d
	ret c
	ret nz
	ld a, l
	cp e
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

Pokedex_StageWrappedGridMapBlocks:
; Pack complete 16-byte map lines while the icon cache's WRAM staging area is
; free. The subsequent HDMAs can then spend exactly one HBlank per line.
	ld hl, .Sources
	ld de, POKEDEX_WRAP_MAP_STAGING
	ld a, POKEDEX_WRAP_MAP_BLOCKS
.next_block
	push af
	ld c, [hl]
	inc hl
	ld b, [hl]
	inc hl
	push hl
	ld h, b
	ld l, c
	ld bc, $10
	call CopyBytes
	pop hl
	pop af
	dec a
	jr nz, .next_block
	ret

.Sources:
	dw wTilemap +  1 * SCREEN_WIDTH
	dw wTilemap +  5 * SCREEN_WIDTH
	dw wTilemap +  6 * SCREEN_WIDTH
	dw wAttrmap +  5 * SCREEN_WIDTH
	dw wAttrmap +  6 * SCREEN_WIDTH
	dw wTilemap +  9 * SCREEN_WIDTH
	dw wTilemap + 10 * SCREEN_WIDTH
	dw wAttrmap +  9 * SCREEN_WIDTH
	dw wAttrmap + 10 * SCREEN_WIDTH
	dw wTilemap + 13 * SCREEN_WIDTH
	dw wTilemap + 14 * SCREEN_WIDTH
	dw wAttrmap + 13 * SCREEN_WIDTH
	dw wAttrmap + 14 * SCREEN_WIDTH

Pokedex_TransferWrappedSelectionName:
	ldh a, [rVBK]
	push af
	ld hl, .Blocks
	ld c, 1
	call Pokedex_TransferWrappedGridBlocksCurrentFrame
	pop af
	ldh [rVBK], a
	ret

.Blocks:
	db 0
	dw POKEDEX_WRAP_MAP_STAGING, vBGMap1 + 1 * TILEMAP_WIDTH

Pokedex_TransferWrappedGridTopRow:
	ldh a, [rVBK]
	push af
	ld hl, .Blocks
	ld c, 4
	call Pokedex_TransferWrappedGridBlocksCurrentFrame
	pop af
	ldh [rVBK], a
	ret

.Blocks:
	db 0
	dw POKEDEX_WRAP_MAP_STAGING + 1 * $10, vBGMap1 + 5 * TILEMAP_WIDTH
	db 0
	dw POKEDEX_WRAP_MAP_STAGING + 2 * $10, vBGMap1 + 6 * TILEMAP_WIDTH
	db BANK(vTiles3)
	dw POKEDEX_WRAP_MAP_STAGING + 3 * $10, vBGMap1 + 5 * TILEMAP_WIDTH
	db BANK(vTiles3)
	dw POKEDEX_WRAP_MAP_STAGING + 4 * $10, vBGMap1 + 6 * TILEMAP_WIDTH

Pokedex_TransferWrappedGridMiddleRow:
	ldh a, [rVBK]
	push af
	ld hl, .Blocks
	ld c, 4
	call Pokedex_TransferWrappedGridBlocksCurrentFrame
	pop af
	ldh [rVBK], a
	ret

.Blocks:
	db 0
	dw POKEDEX_WRAP_MAP_STAGING + 5 * $10, vBGMap1 + 9 * TILEMAP_WIDTH
	db 0
	dw POKEDEX_WRAP_MAP_STAGING + 6 * $10, vBGMap1 + 10 * TILEMAP_WIDTH
	db BANK(vTiles3)
	dw POKEDEX_WRAP_MAP_STAGING + 7 * $10, vBGMap1 + 9 * TILEMAP_WIDTH
	db BANK(vTiles3)
	dw POKEDEX_WRAP_MAP_STAGING + 8 * $10, vBGMap1 + 10 * TILEMAP_WIDTH

Pokedex_TransferWrappedGridBottomRow:
	ldh a, [rVBK]
	push af
	ld hl, .Blocks
	ld c, 4
	call Pokedex_TransferWrappedGridBlocksCurrentFrame
	pop af
	ldh [rVBK], a
	ret

.Blocks:
	db 0
	dw POKEDEX_WRAP_MAP_STAGING + 9 * $10, vBGMap1 + 13 * TILEMAP_WIDTH
	db 0
	dw POKEDEX_WRAP_MAP_STAGING + 10 * $10, vBGMap1 + 14 * TILEMAP_WIDTH
	db BANK(vTiles3)
	dw POKEDEX_WRAP_MAP_STAGING + 11 * $10, vBGMap1 + 13 * TILEMAP_WIDTH
	db BANK(vTiles3)
	dw POKEDEX_WRAP_MAP_STAGING + 12 * $10, vBGMap1 + 14 * TILEMAP_WIDTH

Pokedex_TransferWrappedGridBlocksCurrentFrame:
; hl = packed descriptors: VRAM bank, source, destination; c = block count.
; The wrap scheduler owns the scanline deadline, so do not apply the generic
; cache helper's scanline-127 rollover to these late bottom-row transfers.
.next_block
	ld a, [hli]
	ldh [rVBK], a
	ld a, [hli]
	ld d, a
	ld a, [hli]
	ldh [rVDMA_SRC_HIGH], a
	ld a, d
	and $f0
	ldh [rVDMA_SRC_LOW], a
	ld a, [hli]
	ld e, a
	ld a, [hli]
	and $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, e
	and $f0
	ldh [rVDMA_DEST_LOW], a

	; Queue each block outside HBlank so it consumes the next complete HBlank.
.wait_non_hblank
	ldh a, [rSTAT]
	and STAT_MODE
	jr z, .wait_non_hblank
	ld a, VDMA_LEN_MODE_HBLANK
	ldh [rVDMA_LEN], a
.wait_transfer
	ldh a, [rVDMA_LEN]
	bit B_VDMA_LEN_BUSY, a
	jr z, .wait_transfer
	dec c
	jr nz, .next_block
	ret

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
	ld [wPokedexAnimDictionaryTilesRemaining], a
	ld hl, wPokedexAnimSlotStates
	ld bc, 2
	call ByteFill
	ld a, -1
	ld [wPokedexAnimDisplaySlot], a
	ret

Pokedex_StartAnimationPrefetch:
	ldh a, [hCGB]
	and a
	ret z
	farcall Pokedex_GetSelectedMon
	farcall Pokedex_CheckSeen
	ret z
	ld a, [wTempSpecies]
	ld hl, wPokedexAnimOwner
	cp [hl]
	jr nz, .complete_dictionary
	ld a, [wPokedexAnimProducerState]
	cp POKEDEX_ANIM_PRODUCER_LOADING
	jr z, .initialize
.complete_dictionary
	call Pokedex_CancelAnimationPrefetch
	ld a, [wTempSpecies]
	ld [wPokedexAnimOwner], a
	ld a, POKEDEX_ANIM_PRODUCER_PENDING
	ld [wPokedexAnimProducerState], a
.initialize
	ld a, [wTempSpecies]
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
	cp POKEDEX_ANIM_PRODUCER_LOADING
	jr z, .load_dictionary
	cp POKEDEX_ANIM_PRODUCER_PENDING
	jr z, .initialize
	cp POKEDEX_ANIM_PRODUCER_ACTIVE
	ret nz
	jr .produce

.load_dictionary
	call Pokedex_LoadAnimationDictionaryChunk
	ret

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

Pokedex_LoadAnimationDictionaryChunk:
; Each stream expands to at most six tiles. Input has already been serviced for
; this frame, so a new selection can cancel the job before the next stream.
	ldh a, [rWBK]
	push af
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a
	ld a, [wPokedexAnimDictionaryAddress]
	ld l, a
	ld a, [wPokedexAnimDictionaryAddress + 1]
	ld h, a
	ld a, [wPokedexAnimDictionaryDestination]
	ld e, a
	ld a, [wPokedexAnimDictionaryDestination + 1]
	ld d, a
	ld a, [wPokedexAnimDictionaryBank]
	call FarDecompress
	inc hl
	ld a, l
	ld [wPokedexAnimDictionaryAddress], a
	ld a, h
	ld [wPokedexAnimDictionaryAddress + 1], a
	ld a, e
	ld [wPokedexAnimDictionaryDestination], a
	ld a, d
	ld [wPokedexAnimDictionaryDestination + 1], a
	pop af
	ldh [rWBK], a

	ld hl, wPokedexAnimDictionaryTilesRemaining
	ld a, [hl]
	sub FRONTPIC_ANIM_DICTIONARY_CHUNK_TILES
	jr nc, .store_remaining
	xor a
.store_remaining
	ld [hl], a
	ret nz
	ld a, POKEDEX_ANIM_PRODUCER_PENDING
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
