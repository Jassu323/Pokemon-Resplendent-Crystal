ASSERT POKEDEX_ANIM_SLOT_A_MAP + 7 * 7 == POKEDEX_ANIM_SLOT_A_ATTRS
ASSERT POKEDEX_ANIM_SLOT_A_ATTRS + 7 * 7 == POKEDEX_ANIM_SLOT_B_MAP
ASSERT POKEDEX_ANIM_SLOT_B_MAP + 7 * 7 == POKEDEX_ANIM_SLOT_B_ATTRS
ASSERT POKEDEX_ANIM_SLOT_B_ATTRS + 7 * 7 == POKEDEX_ANIM_SOURCE_TILES
ASSERT POKEDEX_ANIM_SOURCE_TILES + 7 * 7 <= wPokedexWRAM0ScratchEnd
ASSERT POKEDEX_ANIM_PLAN_BUFFER + 2 * 7 * 7 <= POKEDEX_ANIM_SLOT_A_MAP
ASSERT POKEDEX_ANIM_PAYLOAD + POKEDEX_ANIM_UPLOAD_CHUNK_TILES * TILE_SIZE <= POKEDEX_ANIM_PLAN_BUFFER

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
	ld [wPokedexAnimFlags], a
	ld [wPokedexAnimPlaybackState], a
	ld [wPokedexAnimStageSlot], a
	ld [wPokedexAnimStageDuration], a
	ld [wPokedexAnimStagePrehold], a
	ld [wPokedexAnimStageTileCount], a
	ld [wPokedexAnimUploadOffset], a
	ld [wPokedexAnimTrailingHold], a
	ld [wPokedexAnimStageRequiredTiles], a
	ld a, -1
	ld [wPokedexAnimDisplaySlot], a
	ld [wPokedexAnimStageFrameID], a
	ld hl, wPokedexAnimResidentFrameIDs
	ld [hli], a
	ld [hl], a
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
	jr z, .owner_matches
	jp Pokedex_CancelAnimationPrefetch
.owner_matches
	ld a, [wPokedexAnimFlags]
	bit POKEDEX_ANIM_ACTIVE_F, a
	ret nz
	ld a, [wPokedexAnimDictionaryTileCount]
	and a
	ret z
	call Pokedex_CancelAnimationPrefetch
	xor a
	ld [wPokedexAnimProducerPhase], a
	ld a, 1 << POKEDEX_ANIM_ACTIVE_F
	ld [wPokedexAnimFlags], a
	ret

Pokedex_BeginDescriptionAnimation:
	ldh a, [hCGB]
	and a
	ret z
	farcall Pokedex_GetSelectedMon
	farcall Pokedex_CheckSeen
	ret z
	ld a, [wTempSpecies]
	ld hl, wPokedexAnimOwner
	cp [hl]
	ret nz
	call PlayMonCry2
	ld a, [wPokedexAnimDisplaySlot]
	cp -1
	jr z, .no_visual_frame
	ld a, POKEDEX_ANIM_PLAYBACK_PLAYING
	ld [wPokedexAnimPlaybackState], a
	jp Pokedex_PrepareNextAnimationStage

.no_visual_frame
	ld a, POKEDEX_ANIM_PLAYBACK_DONE
	ld [wPokedexAnimPlaybackState], a
	ret

Pokedex_ServiceAnimationProducer:
	ldh a, [hCGB]
	and a
	ret z
	ld a, [wPokedexAnimFlags]
	bit POKEDEX_ANIM_ACTIVE_F, a
	ret z
	call Pokedex_EnsureAnimationStage
	ld a, [wPokedexAnimDictionaryTilesRemaining]
	and a
	jr nz, .service
	ld a, [wPokedexAnimFlags]
	bit POKEDEX_ANIM_STAGE_VALID_F, a
	ret z
	bit POKEDEX_ANIM_STAGE_READY_F, a
	ret nz

.service
	ldh a, [rWBK]
	push af
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a
	ld a, [wPokedexAnimDictionaryTilesRemaining]
	and a
	call nz, Pokedex_LoadAnimationDictionaryChunk
	call Pokedex_GatherReadyAnimationTiles
	pop af
	ldh [rWBK], a

	ld a, c
	and a
	ret z
	ld [wDexTempCounter], a
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	call Pokedex_GetAnimationUploadPointers
	ld a, [wDexTempCounter]
	ld c, a
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .copy_lcd_off
	call Pokedex_HDMATransferAnimationGFX
	jr .transfer_done

.copy_lcd_off
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
.transfer_done
	pop af
	ldh [rVBK], a

	ld a, [wDexTempCounter]
	ld hl, wPokedexAnimUploadOffset
	add [hl]
	ld [hl], a
	ld c, a
	ld a, [wPokedexAnimStageTileCount]
	cp c
	ret nz
	jp Pokedex_FinishAnimationStage

Pokedex_EnsureAnimationStage:
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_PARSER_READY_F, [hl]
	jr nz, .parser_ready
	ld a, [wPokedexAnimOwner]
	ld [wCurPartySpecies], a
	xor a
	ld [wBoxAlignment], a
	ld de, POKEDEX_ANIM_PLAN_BUFFER
	ld b, 0
	ld a, [wPokedexAnimProducerPhase]
	ld c, a
	farcall PokeAnim_InitFrameProducer
	ld [wPokedexAnimFrontpicDim], a
	ld hl, wPokedexAnimFlags
	set POKEDEX_ANIM_PARSER_READY_F, [hl]
	res POKEDEX_ANIM_ENDED_F, [hl]

.parser_ready
	bit POKEDEX_ANIM_STAGE_VALID_F, [hl]
	ret nz
	bit POKEDEX_ANIM_ENDED_F, [hl]
	ret nz
	; fallthrough

Pokedex_PrepareNextAnimationStage:
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_ACTIVE_F, [hl]
	ret z
	bit POKEDEX_ANIM_STAGE_VALID_F, [hl]
	ret nz
	bit POKEDEX_ANIM_ENDED_F, [hl]
	ret nz

	farcall PokeAnim_DecodeNextVisualFrame
	jr nc, .ended
	ld [wPokedexAnimStageDuration], a
	ld a, b
	ld [wPokedexAnimStagePrehold], a
	ld a, e
	ld [wPokedexAnimStageFrameID], a
	xor a
	ld [wPokedexAnimUploadOffset], a
	ld [wPokedexAnimStageRequiredTiles], a
	ld hl, wPokedexAnimFlags
	set POKEDEX_ANIM_STAGE_VALID_F, [hl]
	res POKEDEX_ANIM_STAGE_READY_F, [hl]

	ld a, [wPokedexAnimStageFrameID]
	and a
	jr z, .base_frame
	ld b, a
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationResidentFrameID
	ld a, [hl]
	cp b
	jr z, .resident
	ld [hl], -1
	call Pokedex_BuildAnimationStage
	ld a, [wPokedexAnimStageTileCount]
	and a
	ret nz
	jp Pokedex_FinishAnimationStage

.resident
	xor a
	ld [wPokedexAnimStageTileCount], a
	jp Pokedex_FinishAnimationStage

.base_frame
	call Pokedex_BuildAnimationStage
	jp Pokedex_FinishAnimationStage

.ended
	ld a, b
	ld [wPokedexAnimTrailingHold], a
	ld hl, wPokedexAnimFlags
	set POKEDEX_ANIM_ENDED_F, [hl]
	ret

Pokedex_LoadAnimationDictionaryChunk:
; rWBK is already set to the graphics scratch bank. Each stream expands to at
; most six dictionary tiles so input can cancel before the next service call.
	ld a, [wPokedexAnimDictionaryAddress]
	ld l, a
	ld a, [wPokedexAnimDictionaryAddress + 1]
	ld h, a
	ld a, [wPokedexAnimDictionaryDestination]
	ld e, a
	ld a, [wPokedexAnimDictionaryDestination + 1]
	ld d, a
	ld a, [wPokedexAnimDictionaryTilesRemaining]
	cp FRONTPIC_ANIM_DICTIONARY_CHUNK_TILES
	jr c, .got_chunk_size
	ld a, FRONTPIC_ANIM_DICTIONARY_CHUNK_TILES
.got_chunk_size
	ld c, a
	push bc
	ld a, [wPokedexAnimDictionaryBank]
	call FarDecompress
	inc hl
	pop bc
	ld a, l
	ld [wPokedexAnimDictionaryAddress], a
	ld a, h
	ld [wPokedexAnimDictionaryAddress + 1], a
	ld a, e
	ld [wPokedexAnimDictionaryDestination], a
	ld a, d
	ld [wPokedexAnimDictionaryDestination + 1], a

	ld hl, wPokedexAnimDictionaryTilesRemaining
	ld a, [hl]
	sub c
	ld [hl], a
	ret

Pokedex_BuildAnimationStage:
	call Pokedex_InitializeAnimationStageMap
	xor a
	ld [wPokedexAnimStageTileCount], a
	ld [wPokedexAnimStageRequiredTiles], a
	ld a, [wPokedexAnimStageFrameID]
	and a
	ret z

	ld b, a
	farcall PokeAnim_GetDexFramePlanPointer
	ld a, d
	ld [wDexTempCounter], a
	call GetFarByte
	ld [wDexTempCounter + 1], a
	and a
	ret z
	add a
	ld c, a
	ld b, 0
	inc hl
	ld de, POKEDEX_ANIM_PLAN_BUFFER
	ld a, [wDexTempCounter]
	call FarCopyBytes

	xor a
	ld [wDexTempCounter], a
	ld hl, POKEDEX_ANIM_PLAN_BUFFER

.pair_loop
	ld a, [hli]
	ld e, a
	ld d, 0
	ld a, [hli]
	ld c, a
	push hl
	bit 7, e
	jr nz, .base_tile

	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationSlotMap
	add hl, de
	ld a, [wPokedexAnimStageSlot]
	and a
	ld a, POKEDEX_ANIM_BUFFER_A_TILE
	jr z, .got_buffer_tile
	ld a, POKEDEX_ANIM_BUFFER_B_TILE
.got_buffer_tile
	ld b, a
	ld a, [wPokedexAnimStageTileCount]
	add b
	ld [hl], a
	push bc
	ld bc, 7 * 7
	add hl, bc
	ld [hl], 1 | BG_BANK1
	pop bc

	ld a, [wPokedexAnimStageTileCount]
	ld e, a
	ld d, 0
	ld hl, POKEDEX_ANIM_SOURCE_TILES
	add hl, de
	ld a, c
	ld [hl], a
	inc a
	ld [wPokedexAnimStageRequiredTiles], a
	ld hl, wPokedexAnimStageTileCount
	inc [hl]
	jr .pair_done

.base_tile
	res 7, e
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationSlotMap
	add hl, de
	ld [hl], c

.pair_done
	pop hl

	ld a, [wDexTempCounter]
	inc a
	ld [wDexTempCounter], a
	ld b, a
	ld a, [wDexTempCounter + 1]
	cp b
	jr nz, .pair_loop
	ret

Pokedex_InitializeAnimationStageMap:
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationSlotMap
	ld d, h
	ld e, l
	ld hl, .BaseMap
	ld bc, 7 * 7
	call CopyBytes
	ld h, d
	ld l, e
	ld a, 1
	ld bc, 7 * 7
	call ByteFill
	ret

.BaseMap:
	db  0,  7, 14, 21, 28, 35, 42
	db  1,  8, 15, 22, 29, 36, 43
	db  2,  9, 16, 23, 30, 37, 44
	db  3, 10, 17, 24, 31, 38, 45
	db  4, 11, 18, 25, 32, 39, 46
	db  5, 12, 19, 26, 33, 40, 47
	db  6, 13, 20, 27, 34, 41, 48

Pokedex_GetAnimationBaseTileCount:
	ld a, [wPokedexAnimFrontpicDim]
	ld b, a
	ld c, a
	xor a
.row
	add c
	dec b
	jr nz, .row
	ret

Pokedex_GatherReadyAnimationTiles:
; rWBK is already set to the decompression bank. Return in c the changed tiles
; now ready for one bounded transfer.
	ld c, 0
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_STAGE_VALID_F, [hl]
	ret z
	bit POKEDEX_ANIM_STAGE_READY_F, [hl]
	ret nz
	ld a, [wPokedexAnimDictionaryTileCount]
	ld hl, wPokedexAnimDictionaryTilesRemaining
	sub [hl]
	ld [wDexTempCounter], a
	xor a
	ld [wDexTempCounter + 1], a

	ld a, [wPokedexAnimUploadOffset]
	ld c, a
	ld b, 0
	ld a, c
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, POKEDEX_ANIM_PAYLOAD
	add hl, de
	ld d, h
	ld e, l
	ld a, [wPokedexAnimUploadOffset]
	ld c, a
	ld b, 0
	ld hl, POKEDEX_ANIM_SOURCE_TILES
	add hl, bc

.tile_loop
	ld a, [wPokedexAnimUploadOffset]
	ld b, a
	ld a, [wDexTempCounter + 1]
	add b
	ld b, a
	ld a, [wPokedexAnimStageTileCount]
	cp b
	jr z, .done
	ld a, [wDexTempCounter + 1]
	cp POKEDEX_ANIM_UPLOAD_CHUNK_TILES
	jr z, .done
	ld a, [hli]
	ld b, a
	ld a, [wDexTempCounter]
	cp b
	jr c, .done
	jr z, .done
	push hl
	ld l, b
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld bc, wDecompressScratch
	add hl, bc
	ld b, TILE_SIZE
.copy_tile
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy_tile
	pop hl
	ld a, [wDexTempCounter + 1]
	inc a
	ld [wDexTempCounter + 1], a
	jr .tile_loop

.done
	ld a, [wDexTempCounter + 1]
	ld c, a
	ret

Pokedex_GetAnimationUploadPointers:
	ld a, [wPokedexAnimUploadOffset]
	ld c, a
	ld b, 0
	sla c
	rl b
	sla c
	rl b
	sla c
	rl b
	sla c
	rl b
	ld hl, POKEDEX_ANIM_PAYLOAD
	add hl, bc
	push hl
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationSlotVRAM
	ld h, d
	ld l, e
	add hl, bc
	ld d, h
	ld e, l
	pop hl
	ret

Pokedex_FinishAnimationStage:
	ld a, [wPokedexAnimStageFrameID]
	and a
	jr z, .ready
	ld b, a
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationResidentFrameID
	ld [hl], b
.ready
	ld hl, wPokedexAnimFlags
	set POKEDEX_ANIM_STAGE_READY_F, [hl]
	ret

Pokedex_PrimeDescriptionAnimation:
; Fill the fixed eight-stream runway and make the first visual frame complete.
; Listing prefetch work is retained, so this loop performs only the deficit.
	ldh a, [hCGB]
	and a
	ret z
.loop
	ld a, [wPokedexAnimFlags]
	bit POKEDEX_ANIM_ACTIVE_F, a
	ret z
	call Pokedex_HasAnimationStartupRunway
	ret c
	call Pokedex_ServiceAnimationProducer
	jr .loop

Pokedex_HasAnimationStartupRunway:
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_STAGE_READY_F, [hl]
	jr nz, .check_tiles
	bit POKEDEX_ANIM_ENDED_F, [hl]
	jr nz, .ready
	and a
	ret

.check_tiles
	call Pokedex_GetAnimationBaseTileCount
	ld b, a
	ld a, [wPokedexAnimDictionaryTileCount]
	sub b
	cp POKEDEX_ANIM_STARTUP_TILES
	jr c, .all_tiles
	ld a, b
	add POKEDEX_ANIM_STARTUP_TILES
	jr .check_stage_requirement
.all_tiles
	ld a, [wPokedexAnimDictionaryTileCount]
.check_stage_requirement
	ld b, a
	ld a, [wPokedexAnimStageRequiredTiles]
	cp b
	jr c, .got_target
	ld b, a
.got_target
	ld a, [wPokedexAnimDictionaryTileCount]
	cp b
	jr nc, .target_bounded
	ld b, a
.target_bounded
	ld a, [wPokedexAnimDictionaryTileCount]
	ld hl, wPokedexAnimDictionaryTilesRemaining
	sub [hl]
	cp b
	jr c, .not_ready
.ready
	scf
	ret
.not_ready
	and a
	ret

Pokedex_StageInitialAnimationFrame:
; Install the ready frame into the backing maps before the Selected owner is
; published, so the first visible Description frame is already complete.
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_STAGE_READY_F, [hl]
	ret z
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationSlotMap
	ld d, h
	ld e, l
	farcall Pokedex_StageAnimationFrontpicMap
	ld a, [wPokedexAnimStageSlot]
	ld [wPokedexAnimDisplaySlot], a
	ld a, [wPokedexAnimStageDuration]
	ld [wPokedexAnimPlaybackTimer], a
	ld a, POKEDEX_ANIM_PLAYBACK_WAITING
	ld [wPokedexAnimPlaybackState], a
	ld hl, wPokedexAnimFlags
	res POKEDEX_ANIM_STAGE_VALID_F, [hl]
	res POKEDEX_ANIM_STAGE_READY_F, [hl]
	ld hl, wPokedexAnimStageSlot
	ld a, [hl]
	xor 1
	ld [hl], a
	scf
	ret

Pokedex_UpdateDescriptionAnimation:
	ldh a, [hCGB]
	and a
	ret z
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_MAP_PENDING_F, [hl]
	ret nz
	ld a, [wPokedexAnimPlaybackState]
	cp POKEDEX_ANIM_PLAYBACK_PLAYING
	jr z, .playing
	cp POKEDEX_ANIM_PLAYBACK_MAIN_HOLD
	jr z, .holding
	cp POKEDEX_ANIM_PLAYBACK_PREHOLD
	jr z, .holding
	ret

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
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_STAGE_VALID_F, [hl]
	jr z, .check_phase_end
	ld a, [wPokedexAnimStagePrehold]
	and a
	jr z, .check_stage
	ld [wPokedexAnimHoldTimer], a
	xor a
	ld [wPokedexAnimStagePrehold], a
	ld a, POKEDEX_ANIM_PLAYBACK_PREHOLD
	ld [wPokedexAnimPlaybackState], a
	ret

.check_stage
	bit POKEDEX_ANIM_STAGE_READY_F, [hl]
	jr z, .underrun_stage
	jp Pokedex_InstallAnimationStage

.check_phase_end
	bit POKEDEX_ANIM_ENDED_F, [hl]
	jr z, .underrun_empty
	ld a, [wPokedexAnimTrailingHold]
	and a
	jr z, .phase_finished
	ld [wPokedexAnimHoldTimer], a
	xor a
	ld [wPokedexAnimTrailingHold], a
	ld a, POKEDEX_ANIM_PLAYBACK_PREHOLD
	ld [wPokedexAnimPlaybackState], a
	ret

.phase_finished
	ld a, [wPokedexAnimProducerPhase]
	cp POKEDEX_ANIM_PHASE_MAIN
	jr nz, .finished
	call Pokedex_RestoreBaseFrontpicMap
	ld a, POKEDEX_ANIM_PHASE_IDLE
	ld [wPokedexAnimProducerPhase], a
	ld hl, wPokedexAnimFlags
	res POKEDEX_ANIM_PARSER_READY_F, [hl]
	res POKEDEX_ANIM_ENDED_F, [hl]
	res POKEDEX_ANIM_STAGE_VALID_F, [hl]
	res POKEDEX_ANIM_STAGE_READY_F, [hl]
	xor a
	ld [wPokedexAnimStageSlot], a
	ld a, 18
	ld [wPokedexAnimHoldTimer], a
	ld a, POKEDEX_ANIM_PLAYBACK_MAIN_HOLD
	ld [wPokedexAnimPlaybackState], a
	jp Pokedex_EnsureAnimationStage

.finished
	call Pokedex_RestoreBaseFrontpicMap
	ld a, POKEDEX_ANIM_PLAYBACK_DONE
	ld [wPokedexAnimPlaybackState], a
	ld a, [wPokedexAnimFlags]
	and 1 << POKEDEX_ANIM_MAP_PENDING_F
	ld [wPokedexAnimFlags], a
	ret

.underrun_stage
	call Pokedex_CountAnimationUnderflow
	jp Pokedex_InstallAnimationStage

.underrun_empty
	call Pokedex_CountAnimationUnderflow
	call Pokedex_BuildAnimationUnderflowMap
	jp Pokedex_InstallAnimationStage

Pokedex_CountAnimationUnderflow:
	ld hl, wPokedexAnimUnderflowCount
	inc [hl]
	ret nz
	inc hl
	inc [hl]
	ret

Pokedex_BuildAnimationUnderflowMap:
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationResidentFrameID
	ld [hl], -1
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationSlotMap
	ld d, h
	ld e, l
	ld a, [wPokedexAnimStageSlot]
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
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationSlotMap
	ld bc, 7 * 7
	add hl, bc
	ld a, 1 | BG_BANK1
	ld bc, 7 * 7
	call ByteFill
	ld a, 1
	ld [wPokedexAnimStageDuration], a
	xor a
	ld [wPokedexAnimStagePrehold], a
	ld [wPokedexAnimStageTileCount], a
	ld a, -1
	ld [wPokedexAnimStageFrameID], a
	ld hl, wPokedexAnimFlags
	set POKEDEX_ANIM_STAGE_VALID_F, [hl]
	res POKEDEX_ANIM_STAGE_READY_F, [hl]
	ret

Pokedex_InstallAnimationStage:
	ld a, [wPokedexAnimStageSlot]
	call Pokedex_GetAnimationSlotMap
	ld d, h
	ld e, l
	farcall Pokedex_CommitAnimationFrontpicMap
	ld a, [wPokedexAnimStageSlot]
	ld [wPokedexAnimDisplaySlot], a
	ld a, [wPokedexAnimStageDuration]
	ld [wPokedexAnimPlaybackTimer], a
	ld hl, wPokedexAnimFlags
	res POKEDEX_ANIM_STAGE_VALID_F, [hl]
	res POKEDEX_ANIM_STAGE_READY_F, [hl]
	ld hl, wPokedexAnimStageSlot
	ld a, [hl]
	xor 1
	ld [hl], a
	jp Pokedex_PrepareNextAnimationStage

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

Pokedex_GetAnimationResidentFrameID:
	ld hl, wPokedexAnimResidentFrameIDs
	jr Pokedex_AddAnimationSlotOffset

Pokedex_AddAnimationSlotOffset:
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
