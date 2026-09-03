LoadSGBPokedexGFX:
	ld hl, SGBPokedexGFX_LZ
	ld de, vTiles2 tile $31
	call Decompress
	ret

LoadSGBPokedexGFX2:
	ld hl, SGBPokedexGFX_LZ
	ld de, vTiles2 tile $31
	lb bc, BANK(SGBPokedexGFX_LZ), 58
	call DecompressRequest2bpp
	ret

SGBPokedexGFX_LZ:
INCBIN "gfx/pokedex/pokedex_sgb.2bpp.lz"

ASSERT POKEDEX_GRID_CENTER_GFX + 8 tiles == POKEDEX_GRID_SIDE_FRAME0_GFX
ASSERT POKEDEX_GRID_SIDE_FRAME0_GFX + 8 tiles == POKEDEX_GRID_SIDE_FRAME1_GFX
ASSERT POKEDEX_GRID_SIDE_FRAME1_GFX + 8 tiles <= wPokedexWRAM0ScratchEnd

Pokedex_InitGridCacheState:
	ld hl, wPokedexGridCacheRowOffsets
	ld bc, 2 * POKEDEX_GRID_CACHE_ROWS + 2
	ld a, -1
	call ByteFill
	xor a
	ld [wPokedexGridTopPhysicalRow], a
	ld [wPokedexGridPendingPhysicalRow], a
	ret

Pokedex_CopyBackingToWindow:
	ld hl, vBGMap1
	jr Pokedex_CopyBackingToMap

Pokedex_CopyBackingToBG:
	ld hl, vBGMap0
	; fallthrough

Pokedex_CopyBackingToMap:
; Copy the complete backing tilemap and attrmap without borrowing the Pack
; transfer scratch, which aliases the resident animation dictionary.
	ldh a, [hBGMapAddress]
	ld e, a
	ldh a, [hBGMapAddress + 1]
	ld d, a
	push de
	ld a, l
	ldh [hBGMapAddress], a
	ld a, h
	ldh [hBGMapAddress + 1], a
	call CopyTilemapAtOnce
	pop de
	ld a, e
	ldh [hBGMapAddress], a
	ld a, d
	ldh [hBGMapAddress + 1], a
	ret

Pokedex_NormalizeListingAfterSelectedMon:
; Restore the closest aligned Listing viewport containing the absolute entry
; returned by the Selected Mon owner.
	ld hl, wPokedexSelectedIndex
	ld a, [hli]
	ld e, a
	ld d, [hl]
	ld a, e
	ld [wDexTempCounter], a
	ld a, d
	ld [wDexTempCounter + 1], a

	ld hl, wPokedexListingSavedScrollOffset
	ld a, [hli]
	ld c, a
	ld b, [hl]
	ld a, d
	cp b
	jr c, .above_saved_view
	jr nz, .check_below_saved_view
	ld a, e
	cp c
	jr c, .above_saved_view

.check_below_saved_view
	ld h, b
	ld l, c
	ld bc, POKEDEX_GRID_SIZE
	add hl, bc
	ld a, d
	cp h
	jr c, .use_saved_view
	jr nz, .below_saved_view
	ld a, e
	cp l
	jr c, .use_saved_view

.below_saved_view
	call .GetSelectedRowStart
	ld bc, -2 * POKEDEX_GRID_WIDTH
	add hl, bc
	jr .store_view

.above_saved_view
	call .GetSelectedRowStart
	jr .store_view

.use_saved_view
	ld hl, wPokedexListingSavedScrollOffset
	ld a, [hli]
	ld h, [hl]
	ld l, a

.store_view
	ld a, l
	ld [wDexListingScrollOffset], a
	ld c, a
	ld a, h
	ld [wDexListingScrollOffset + 1], a
	ld b, a
	ld a, [wDexTempCounter]
	sub c
	ld e, a
	ld a, [wDexTempCounter + 1]
	sbc b
	ld a, e
	ld [wDexListingCursor], a
	ret

.GetSelectedRowStart:
	ld a, e
	add d ; 256 % 3 = 1
	jr nc, .reduce_remainder
	inc a
.reduce_remainder
	cp POKEDEX_GRID_WIDTH
	jr c, .got_remainder
	sub POKEDEX_GRID_WIDTH
	jr .reduce_remainder
.got_remainder
	ld l, e
	ld h, d
	ld c, a
	ld a, l
	sub c
	ld l, a
	ret nc
	dec h
	ret

Pokedex_EnsureGridCache:
; Reuse a complete five-row cache when the Listing viewport is still inside
; it. Detail paging can move farther away, in which case the cache is primed
; again before the Listing is revealed.
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld hl, wPokedexGridCacheRowOffsets
	ld b, POKEDEX_GRID_CACHE_ROWS
	ld c, 0
.find_top
	ld a, [hli]
	cp e
	jr nz, .next_top
	ld a, [hl]
	cp d
	jr z, .found_top
.next_top
	inc hl
	inc c
	dec b
	jr nz, .find_top
	jp Pokedex_PrimeGridCache

.found_top
	ld a, c
	ld [wPokedexGridTopPhysicalRow], a
	ld [wDexTempCounter], a

	; Validate the row above the viewport.
	and a
	jr nz, .got_previous_physical
	ld a, POKEDEX_GRID_CACHE_ROWS
.got_previous_physical
	dec a
	ld b, a
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, d
	and a
	jr nz, .subtract_previous
	ld a, e
	cp POKEDEX_GRID_WIDTH
	jr nc, .subtract_previous
	ld de, -1
	jr .check_previous
.subtract_previous
	ld a, e
	sub POKEDEX_GRID_WIDTH
	ld e, a
	jr nc, .check_previous
	dec d
.check_previous
	call .CheckRowTag
	jp nc, Pokedex_PrimeGridCache

	; Validate the top row and the three rows after it.
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, [wDexTempCounter]
	ld b, a
	ld c, 4
.check_forward
	call .CheckRowTag
	jp nc, Pokedex_PrimeGridCache
	ld a, b
	inc a
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .got_next_physical
	xor a
.got_next_physical
	ld b, a
	ld a, e
	add POKEDEX_GRID_WIDTH
	ld e, a
	jr nc, .no_forward_carry
	inc d
.no_forward_carry
	dec c
	jr nz, .check_forward
	scf
	ret

.CheckRowTag:
; b = physical row, de = expected absolute Listing row offset.
	push hl
	ld a, b
	add a
	ld l, a
	ld h, 0
	ld a, LOW(wPokedexGridCacheRowOffsets)
	add l
	ld l, a
	ld a, HIGH(wPokedexGridCacheRowOffsets)
	adc h
	ld h, a
	ld a, [hli]
	cp e
	jr nz, .tag_mismatch
	ld a, [hl]
	cp d
	jr nz, .tag_mismatch
	pop hl
	scf
	ret
.tag_mismatch
	pop hl
	and a
	ret

Pokedex_PrimeGridCache:
; Physical row 1 is the top visible row. Row 0 is the look-behind cache and
; rows 2-4 are the two other visible rows plus look-ahead cache. Prime the
; complete cache with the LCD off; the VBlank-only DMA path is reserved for a
; single scrolling refill.
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .prime
	call DisableLCD
	call .prime
	call EnableLCD
	scf
	ret

.prime
	ld a, 1
	ld [wPokedexGridTopPhysicalRow], a
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, d
	and a
	jr nz, .prime_previous
	ld a, e
	cp POKEDEX_GRID_WIDTH
	jr nc, .prime_previous
	ld de, -1
	jr .stage_previous
.prime_previous
	ld a, e
	sub POKEDEX_GRID_WIDTH
	ld e, a
	jr nc, .stage_previous
	dec d
.stage_previous
	xor a
	call Pokedex_PrepareGridCacheRow
	call Pokedex_UploadPendingGridCacheRow

	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld b, 1
.prime_forward
	ld a, b
	push bc
	push de
	call Pokedex_PrepareGridCacheRow
	call Pokedex_UploadPendingGridCacheRow
	pop de
	pop bc
	ld a, e
	add POKEDEX_GRID_WIDTH
	ld e, a
	jr nc, .no_prime_carry
	inc d
.no_prime_carry
	inc b
	ld a, b
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .prime_forward
	scf
	ret

Pokedex_CacheGridIconPalette:
; Resolve each visible slot's icon palette when its stable species ID is
; cached, so the scroll transaction never reconstructs palettes from IDs that
; may have moved in the conversion table.
	ld a, [wDexTempCounter]
	ld e, a
	ld d, 0
	ld hl, wPokedexGridFlags
	add hl, de
	bit POKEDEX_GRID_SEEN_F, [hl]
	ret z
	ld hl, wPokedexGridSpecies
	add hl, de
	ld c, [hl]
	push de
	farcall ReadMonMenuIconForPokedex
	ld a, c
	swap a
	and $f
	ld c, a
	pop de
	ld hl, wPokedexGridIconPalettes
	add hl, de
	ld [hl], c
	ret

Pokedex_PrepareGridCacheRefill:
; The row entering the visible viewport is already resident. Stage the new
; look-ahead/look-behind row into the physical slot that just moved offscreen.
	ld a, [wPokedexGridScrollDirection]
	cp POKEDEX_GRID_SCROLL_DOWN
	jr z, .scrolling_down
	cp POKEDEX_GRID_SCROLL_WRAP_DOWN
	jr z, .scrolling_down
	ld a, [wPokedexGridTopPhysicalRow]
	and a
	jr nz, .got_up_physical
	ld a, POKEDEX_GRID_CACHE_ROWS
.got_up_physical
	dec a
	ld b, a
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, d
	and a
	jr nz, .subtract_up_offset
	ld a, e
	cp POKEDEX_GRID_WIDTH
	jr nc, .subtract_up_offset
	ld de, -1
	jr .prepare
.subtract_up_offset
	ld a, e
	sub POKEDEX_GRID_WIDTH
	ld e, a
	jr nc, .prepare
	dec d
	jr .prepare

.scrolling_down
	ld a, [wPokedexGridTopPhysicalRow]
	add POKEDEX_GRID_HEIGHT
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .got_down_physical
	sub POKEDEX_GRID_CACHE_ROWS
.got_down_physical
	ld b, a
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, e
	add POKEDEX_GRID_SIZE
	ld e, a
	jr nc, .prepare
	inc d
.prepare
	ld a, b
	; fallthrough

Pokedex_PrepareGridCacheRow:
; a = physical cache row, de = absolute Listing offset or $ffff for empty.
	ld [wPokedexGridPendingPhysicalRow], a
	ld a, e
	ld [wPokedexGridPendingRowOffset], a
	ld a, d
	ld [wPokedexGridPendingRowOffset + 1], a
	call Pokedex_InvalidatePendingGridCacheRow
	ld hl, POKEDEX_GRID_CENTER_GFX
	ld bc, 3 * 8 tiles
	xor a
	call ByteFill
	ld a, [wPokedexGridPendingRowOffset]
	ld b, a
	ld a, [wPokedexGridPendingRowOffset + 1]
	and b
	inc a
	ret z
	xor a
	ld [wDexTempCounter], a
.loop
	ld hl, wPokedexGridPendingRowOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, [wDexTempCounter]
	add e
	ld e, a
	jr nc, .got_entry_offset
	inc d
.got_entry_offset
	call .GetSeenSpeciesAtOffset
	jr z, .next
	ld c, a
	farcall ReadMonMenuIconForPokedex
	ld a, b
	ldh [hTempBank], a
	ld h, d
	ld l, e
	ld a, [wDexTempCounter]
	cp 1
	jr z, .copy_center
	push hl
	add a
	ld e, a
	ld d, 0
	ld hl, .SideFrame0StagingDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	pop hl
	ld bc, 4 tiles
	ldh a, [hTempBank]
	call FarCopyBytes
	push hl
	ld a, [wDexTempCounter]
	add a
	ld e, a
	ld d, 0
	ld hl, .SideFrame1StagingDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	pop hl
	ld bc, 4 tiles
	ldh a, [hTempBank]
	call FarCopyBytes
	jr .next

.copy_center
	ld de, POKEDEX_GRID_CENTER_GFX
	ld bc, 8 tiles
	ldh a, [hTempBank]
	call FarCopyBytes
.next
	ld hl, wDexTempCounter
	inc [hl]
	ld a, [hl]
	cp POKEDEX_GRID_WIDTH
	jr c, .loop
	ret
	.GetSeenSpeciesAtOffset:
; de = absolute Listing entry offset. Return nz and a = species when seen.
	ld hl, wDexListingEnd
	ld a, e
	sub [hl]
	inc hl
	ld a, d
	sbc [hl]
	jr nc, .not_seen
	ld h, d
	ld l, e
	add hl, hl
	ld de, wPokedexOrder
	add hl, de
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOrder)
	ldh [rSVBK], a
	ld a, [hli]
	ld c, a
	ld b, [hl]
	pop af
	ldh [rSVBK], a
	ld a, b
	and c
	inc a
	jr z, .not_seen
	ld h, b
	ld l, c
	push bc
	call GetPokemonIDFromIndex
	ld [wTempSpecies], a
	pop de
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexSeen)
	ldh [rSVBK], a
	call CheckSeenMonIndex
	pop af
	ldh [rSVBK], a
	jr z, .not_seen
	ld a, [wTempSpecies]
	inc a ; force nz while preserving the species through the decrement
	dec a
	ret
.not_seen
	xor a
	ret

.SideFrame0StagingDestinations:
	dw POKEDEX_GRID_SIDE_FRAME0_GFX
	dw 0
	dw POKEDEX_GRID_SIDE_FRAME0_GFX + 4 tiles

.SideFrame1StagingDestinations:
	dw POKEDEX_GRID_SIDE_FRAME1_GFX
	dw 0
	dw POKEDEX_GRID_SIDE_FRAME1_GFX + 4 tiles

Pokedex_InvalidatePendingGridCacheRow:
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld e, a
	ld d, 0
	ld hl, wPokedexGridCacheRowOffsets
	add hl, de
	ld a, -1
	ld [hli], a
	ld [hl], a
	ret

Pokedex_UploadPendingGridCacheRow:
; Upload both frames of the staged icon row and publish its ownership tag only
; after every BG and OBJ chunk has reached VRAM bank 1.
	ldh a, [rVBK]
	push af
	ld a, BANK(vTiles3)
	ldh [rVBK], a
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .lcd_off
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld e, a
	ld d, 0
	ld hl, .SideFrame0RowDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ld hl, POKEDEX_GRID_SIDE_FRAME0_GFX
	ld c, 8
	call Pokedex_HDMATransferCacheGFX
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld e, a
	ld d, 0
	ld hl, .CenterRowDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ld hl, POKEDEX_GRID_CENTER_GFX
	ld c, 8
	call Pokedex_HDMATransferCacheGFX
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld e, a
	ld d, 0
	ld hl, .SideFrame1RowDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ld hl, POKEDEX_GRID_SIDE_FRAME1_GFX
	ld c, 8
	call Pokedex_HDMATransferCacheGFX
	jr .publish

.lcd_off
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld e, a
	ld d, 0
	ld hl, .SideFrame0RowDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ld hl, POKEDEX_GRID_SIDE_FRAME0_GFX
	ld bc, 8 tiles
	call CopyBytes
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld e, a
	ld d, 0
	ld hl, .CenterRowDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ld hl, POKEDEX_GRID_CENTER_GFX
	ld bc, 8 tiles
	call CopyBytes
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld e, a
	ld d, 0
	ld hl, .SideFrame1RowDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ld hl, POKEDEX_GRID_SIDE_FRAME1_GFX
	ld bc, 8 tiles
	call CopyBytes

.publish
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld e, a
	ld d, 0
	ld hl, wPokedexGridCacheRowOffsets
	add hl, de
	ld a, [wPokedexGridPendingRowOffset]
	ld [hli], a
	ld a, [wPokedexGridPendingRowOffset + 1]
	ld [hl], a
	pop af
	ldh [rVBK], a
	ret

.CenterRowDestinations:
	dw vTiles3 tile (POKEDEX_CENTER_ICON_TILE + 0 * 8)
	dw vTiles3 tile (POKEDEX_CENTER_ICON_TILE + 1 * 8)
	dw vTiles3 tile (POKEDEX_CENTER_ICON_TILE + 2 * 8)
	dw vTiles3 tile (POKEDEX_CENTER_ICON_TILE + 3 * 8)
	dw vTiles3 tile (POKEDEX_CENTER_ICON_TILE + 4 * 8)

.SideFrame0RowDestinations:
	dw vTiles5 tile (POKEDEX_SIDE_ICON_TILE + 0 * 8)
	dw vTiles5 tile (POKEDEX_SIDE_ICON_TILE + 1 * 8)
	dw vTiles5 tile (POKEDEX_SIDE_ICON_TILE + 2 * 8)
	dw vTiles5 tile (POKEDEX_SIDE_ICON_TILE + 3 * 8)
	dw vTiles5 tile (POKEDEX_SIDE_ICON_TILE + 4 * 8)

.SideFrame1RowDestinations:
	dw vTiles4 tile (POKEDEX_SIDE_ICON_FRAME1_VRAM_TILE + 0 * 8)
	dw vTiles4 tile (POKEDEX_SIDE_ICON_FRAME1_VRAM_TILE + 1 * 8)
	dw vTiles4 tile (POKEDEX_SIDE_ICON_FRAME1_VRAM_TILE + 2 * 8)
	dw vTiles4 tile (POKEDEX_SIDE_ICON_FRAME1_VRAM_TILE + 3 * 8)
	dw vTiles4 tile (POKEDEX_SIDE_ICON_FRAME1_VRAM_TILE + 4 * 8)

Pokedex_CommitWrappedSelectionGFX:
; LCD-off fallback for the wrapped Listing reveal. The live-screen path owns
; this transfer from the Pokédex VBlank transaction below.
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles2
	ld bc, 7 * 7 tiles
	call CopyBytes
	pop af
	ldh [rVBK], a
	ret

Pokedex_PrepareWrappedGridRows:
; Reinterpret the existing five-row ring without reserving more VRAM:
; old P+3/P+4 become destination top/middle, and old P becomes bottom.
	ld a, [wPokedexGridTopPhysicalRow]
	add POKEDEX_GRID_HEIGHT
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .got_top_physical
	sub POKEDEX_GRID_CACHE_ROWS
.got_top_physical
	ld b, a
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, b
	call Pokedex_PrepareGridCacheRow
	call Pokedex_UploadPendingGridCacheRow

	ld a, [wPokedexGridTopPhysicalRow]
	add POKEDEX_GRID_HEIGHT + 1
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .got_middle_physical
	sub POKEDEX_GRID_CACHE_ROWS
.got_middle_physical
	ld b, a
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, e
	add POKEDEX_GRID_WIDTH
	ld e, a
	jr nc, .got_middle_offset
	inc d
.got_middle_offset
	ld a, b
	call Pokedex_PrepareGridCacheRow
	call Pokedex_UploadPendingGridCacheRow

	ld a, [wPokedexGridTopPhysicalRow]
	ld b, a
	ld hl, wDexListingScrollOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, e
	add 2 * POKEDEX_GRID_WIDTH
	ld e, a
	jr nc, .got_bottom_offset
	inc d
.got_bottom_offset
	ld a, b
	call Pokedex_PrepareGridCacheRow

	ld hl, wPokedexGridTopPhysicalRow
	ld a, [hl]
	add POKEDEX_GRID_HEIGHT
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .set_new_top
	sub POKEDEX_GRID_CACHE_ROWS
.set_new_top
	ld [hl], a
	ret

Pokedex_UploadWrappedBottomRow:
; The pending row owns the old top physical slots. Begin only after every old
; top-row BG/OBJ pixel has been scanned, leaving ample HBlank time to finish.
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jp z, Pokedex_UploadPendingGridCacheRow
	ldh a, [rLY]
	cp 56
	jr c, .wait_row_end
.wait_next_frame
	ldh a, [rLY]
	cp 56
	jr nc, .wait_next_frame
.wait_row_end
	ldh a, [rLY]
	cp 56
	jr c, .wait_row_end
	jp Pokedex_UploadPendingGridCacheRow

Pokedex_FinalizeWrappedGridCache:
; Refill the one real neighbor row and invalidate the opposite endpoint row.
	call Pokedex_PrepareGridCacheRefill
	call Pokedex_UploadPendingGridCacheRow
	ld a, [wPokedexGridScrollDirection]
	cp POKEDEX_GRID_SCROLL_WRAP_DOWN
	jr z, .invalidate_previous
	ld a, [wPokedexGridTopPhysicalRow]
	add POKEDEX_GRID_HEIGHT
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .invalidate
	sub POKEDEX_GRID_CACHE_ROWS
	jr .invalidate
.invalidate_previous
	ld a, [wPokedexGridTopPhysicalRow]
	and a
	jr nz, .decrement
	ld a, POKEDEX_GRID_CACHE_ROWS
.decrement
	dec a
.invalidate
	add a
	ld e, a
	ld d, 0
	ld hl, wPokedexGridCacheRowOffsets
	add hl, de
	ld a, -1
	ld [hli], a
	ld [hl], a
	ret

LoadQuestionMarkPic:
	ld hl, .QuestionMarkLZ
	ld de, sScratch
	call Decompress
	ret

.QuestionMarkLZ:
INCBIN "gfx/pokedex/question_mark.2bpp.lz"

Pokedex_CommitStagedSelection:
; Keep the old name and frontpic intact through their visible scanlines, then
; replace both later in the same frame. Palette and cursor OAM are queued by
; the caller for the following VBlank, revealing one complete new selection.
; If staging finishes before the frontpic's final scanline, upload the frontpic
; and then replace the already-scanned name in the current frame. Otherwise
; retain the full next-frame schedule.
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .lcd_off

	ldh a, [rLY]
	cp 64
	jr nc, .wait_next_frame

.wait_fast_frontpic_row
	ldh a, [rLY]
	cp 64
	jr c, .wait_fast_frontpic_row
	call .commit_frontpic
	call Pokedex_CommitStagedSelectionName
	ret

.wait_next_frame
	ldh a, [rLY]
	cp 16
	jr nc, .wait_next_frame

.wait_name_row
	ldh a, [rLY]
	cp 16
	jr c, .wait_name_row
	call Pokedex_CommitStagedSelectionName

.wait_frontpic_row
	ldh a, [rLY]
	cp 64
	jr c, .wait_frontpic_row

.commit_frontpic
	jp Pokedex_CommitPreparedSelectedMonGFX

.lcd_off
	hlcoord 0, 1
	ld de, vBGMap1 + TILEMAP_WIDTH
	ld bc, 11
	call CopyBytes
	; fallthrough

Pokedex_CommitPreparedSelectedMonGFX::
; Publish the prepared base frontpic and footprint without touching either
; owner's tilemaps. This is shared by cold Listing setup and hidden Selected
; staging, where the complete map is committed separately.
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .copy_frontpic
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles2
	ld c, 7 * 7
	call Pokedex_HDMATransferFrontpic
	jr .frontpic_ready

.copy_frontpic
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles2
	ld bc, 7 * 7 tiles
	call CopyBytes

.frontpic_ready
	ld a, [wCurPartySpecies]
	cp -1
	jr z, .done
	ld a, BANK(vTiles4)
	ldh [rVBK], a
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .copy_footprint
	ld hl, wPokedexWRAM0Scratch + 7 * 7 tiles
	ld de, vTiles4 tile $31
	ld c, 4
	call Pokedex_HDMATransferSelectionGFX
	jr .footprint_ready

.copy_footprint
	ld hl, wPokedexWRAM0Scratch + 7 * 7 tiles
	ld de, vTiles4 tile $31
	ld bc, 4 tiles
	call CopyBytes

.footprint_ready
	ld a, [wCurPartySpecies]
	ld [wPokedexResidentFootprintSpecies], a

.done
	pop af
	ldh [rVBK], a
	ret

Pokedex_PrepareAndCommitSelectedMonGFX::
	farcall Pokedex_PrepareSelectedMonTiles
	jp Pokedex_CommitPreparedSelectedMonGFX

Pokedex_CommitStagedSelectionName:
; Commit only the Listing header after its visible scanline has passed.
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	hlcoord 0, 1
	ld de, vBGMap1 + TILEMAP_WIDTH
	ld c, 11
.copy_name
.wait_vram
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_vram
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .copy_name
	pop af
	ldh [rVBK], a
	ret

Pokedex_CommitAnimationFrontpicMap::
; de = packed 7x7 tilemap immediately followed by packed attributes.
	call Pokedex_StageAnimationFrontpicMap
	jr Pokedex_CommitCurrentFrontpicMap

Pokedex_StageAnimationFrontpicMap::
; Patch only the owner backing maps. The caller can stage this before an
; atomic owner transition without exposing a partially installed frame.
	ld h, d
	ld l, e
	push hl
	decoord 1, 1
	call Pokedex_CopyPackedFrontpicMapToBacking
	pop hl
	ld bc, 7 * 7
	add hl, bc
	decoord 1, 1, wAttrmap
	call Pokedex_CopyPackedFrontpicMapToBacking
	ret

Pokedex_CommitCurrentFrontpicMap::
; Publish the prepared tilemap and attributes together in VBlank. The
; graphics upload has already completed (or deliberately underrun).
	xor a
	ldh [hBGMapMode], a
	call Pokedex_StageCurrentFrontpicOwnerMaps
	ld hl, wPokedexAnimFlags
	set POKEDEX_ANIM_MAP_PENDING_F, [hl]
	ld a, VBLANK_POKEDEX
	ldh [hVBlank], a
	ret

Pokedex_StageCurrentFrontpicOwnerMaps:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a
	hlcoord 1, 1
	ld de, wPokedexOwnerTilemapBuffer + TILEMAP_WIDTH + 1
	call .CopyMap
	hlcoord 1, 1, wAttrmap
	ld de, wPokedexOwnerAttrmapBuffer + TILEMAP_WIDTH + 1
	call .CopyMap
	pop af
	ldh [rSVBK], a
	ret

.CopyMap:
	ld b, 7
.row
	ld c, 7
.col
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .col
	push bc
	ld bc, SCREEN_WIDTH - 7
	add hl, bc
	pop bc
	ld a, e
	add TILEMAP_WIDTH - 7
	ld e, a
	jr nc, .no_dest_carry
	inc d
.no_dest_carry
	dec b
	jr nz, .row
	ret

Pokedex_CopyPackedFrontpicMapToBacking:
	ld b, 7
.backing_row
	ld c, 7
.backing_col
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .backing_col
	ld a, e
	add SCREEN_WIDTH - 7
	ld e, a
	jr nc, .no_backing_carry
	inc d
.no_backing_carry
	dec b
	jr nz, .backing_row
	ret

Pokedex_SyncGridIconAnimationFrame:
; Stage the phase that will be current after the next VBlank. Selection and
; scrolling reveals use the same clock as the interrupt-owned idle animator.
	ldh a, [hCGB]
	and a
	ret z
	ldh a, [hVBlankCounter]
	inc a
	and 1 << POKEDEX_GRID_ICON_ANIM_FRAME_F
	ld [wPokedexGridIconAnimFrame], a
	ret

Pokedex_StageGridIconAnimation:
; Build the tilemap and center-column shadow OAM for the synchronized phase.
	ldh a, [hCGB]
	and a
	ret z
	call Pokedex_DrawListGrid
	jp Pokedex_UpdateCenterIconAnimationOAM

Pokedex_StageOwnerTransitionMaps::
; Convert both 20x18 backing maps to VRAM's 32-byte row stride in the
; Pokedex-only bank 3 overlay.
	ldh a, [rSVBK]
	push af
	ldh a, [hMapObjectIndex]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a
	decoord 0, 0, wAttrmap
	ld hl, wPokedexOwnerAttrmapBuffer
	ld c, 0
	call .PadMap
	decoord 0, 0
	ld hl, wPokedexOwnerTilemapBuffer
	ld c, ' '
	call .PadMap
	pop af
	ldh [hMapObjectIndex], a
	pop af
	ldh [rSVBK], a
	ret

.PadMap:
	ld a, c
	ldh [hMapObjectIndex], a
	ld c, SCREEN_HEIGHT
.next_row
	ld b, SCREEN_WIDTH
.copy_visible
	ld a, [de]
	inc de
	ld [hli], a
	dec b
	jr nz, .copy_visible
	ldh a, [hMapObjectIndex]
	ld b, TILEMAP_WIDTH - SCREEN_WIDTH
.pad_row
	ld [hli], a
	dec b
	jr nz, .pad_row
	dec c
	jr nz, .next_row
	ret

ASSERT BANK(wPokedexOwnerTilemapBuffer) == 3
ASSERT BANK(wPokedexOwnerAttrmapBuffer) == 3
ASSERT (LOW(wPokedexOwnerTilemapBuffer) & $f) == 0
ASSERT (LOW(wPokedexOwnerAttrmapBuffer) & $f) == 0

Pokedex_PublishOrStageDescriptionBacking::
	ldh a, [hCGB]
	and a
	jr z, .publish
	call Pokedex_StageOwnerTransitionMaps
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_ENTERING
	jr nz, .publish
	ld a, [wPokedexSelectedReturnState]
	cp DEXSTATE_MAIN_SCR
	jr nz, .publish
	ld a, POKEDEX_OWNER_TRANSITION_DESCRIPTION
	call Pokedex_QueueOwnerTransition
	xor a
	ldh [hVBlank], a
	scf
	ret
.publish
	call Pokedex_CopyBackingToBG
	and a
	ret

Pokedex_PublishOrStageListingBacking::
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_LEAVING
	jp z, Pokedex_StageOwnerTransitionMaps
	jp Pokedex_CopyBackingToBG

Pokedex_RevealOrCommitListing::
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_LEAVING
	jr nz, .cold
	ld a, POKEDEX_OWNER_TRANSITION_LISTING
	jp Pokedex_QueueOwnerTransition
.cold
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ld a, $47
	ldh [hWX], a
	xor a
	ldh [hOAMUpdate], a
	call DelayFrame
	xor a
	ld [wPokedexSelectedBGPaletteDirty], a
	ld [wPokedexSelectedOBJPaletteDirty], a
	ret

Pokedex_BlackOutSelectedMonBG::
	ld hl, wPokedexSelectedBGPaletteDirty
	ld a, [hl]
	or POKEDEX_SELECTED_EXTENDED_BG_PALS
	ld [hl], a
	ld a, POKEDEX_LISTING_OBJ_PALS
	ld [wPokedexSelectedOBJPaletteDirty], a
	farcall Pokedex_BlackOutBG
	ret

Pokedex_VBlankDispatch::
	call Pokedex_VBlankOwnerTransition
	ret c
	call Pokedex_VBlankAnimationFrontpicMap
	ret c
	jp Pokedex_VBlankGridIconAnimation

Pokedex_QueueOwnerTransition::
; a = POKEDEX_OWNER_TRANSITION_*. The staged maps, palette targets, and
; shadow OAM must all be complete before publishing the request.
	ld [wPokedexOwnerTransition], a
	xor a
	ldh [hBGMapMode], a
	ldh [hCGBPalUpdate], a
	ld a, TRUE
	ldh [hOAMUpdate], a
	ld a, VBLANK_POKEDEX
	ldh [hVBlank], a
.wait
	call DelayFrame
	ld a, [wPokedexOwnerTransition]
	and a
	jr nz, .wait
	xor a
	ldh [hOAMUpdate], a
	ret

Pokedex_VBlankOwnerTransition::
; Publish one complete BG0 owner while the LCD is in VBlank. Return carry
; when committed so the dispatcher skips Listing animation. Publish the
; prepared shadow OAM here before VBlank_Normal performs its bookkeeping.
	ld a, [wPokedexOwnerTransition]
	and a
	ret z
	ldh a, [hBGMapUpdate]
	and a
	ret nz
	ldh a, [hDMATransfer]
	and a
	ret nz
	ldh a, [rLY]
	cp LY_VBLANK + 1
	ret nc
	ld a, [wPokedexOwnerTransition]
	cp POKEDEX_OWNER_TRANSITION_LISTING
	ld a, $47
	jr z, .got_wx
	ld a, $a7
.got_wx
	ldh [hWX], a
	ldh [rWX], a
	xor a
	ldh [hWY], a
	ldh [rWY], a

	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af

	ld a, BANK(wPokedexOwnerAttrmapBuffer)
	ldh [rSVBK], a
	ld a, BANK(vBGMap2)
	ldh [rVBK], a
	ld hl, wPokedexOwnerAttrmapBuffer
	call .TransferMap
	xor a
	ldh [rVBK], a
	ld hl, wPokedexOwnerTilemapBuffer
	call .TransferMap

	ld a, BANK(wBGPals2)
	ldh [rSVBK], a
	call .CommitDirtyBGPals
	call .CommitDirtyOBPals

	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	call hTransferShadowOAM
	ld a, TRUE
	ldh [hOAMUpdate], a
	xor a
	ld [wPokedexOwnerTransition], a
	ld [wPokedexSelectedBGPaletteDirty], a
	ld [wPokedexSelectedOBJPaletteDirty], a
	scf
	ret

.CommitDirtyBGPals:
	ld a, [wPokedexSelectedBGPaletteDirty]
	and a
	ret z
	ld a, BGPI_AUTOINC palette 2
	ldh [rBGPI], a
	ld hl, wBGPals2 palette 2
	ld c, LOW(rBGPD)
	rept 6 palettes
		ld a, [hli]
		ldh [c], a
	endr
	ret

.CommitDirtyOBPals:
	ld a, [wPokedexSelectedOBJPaletteDirty]
	and a
	ret z
	ld a, OBPI_AUTOINC palette 0
	ldh [rOBPI], a
	ld hl, wOBPals2 palette 0
	ld c, LOW(rOBPD)
	rept 6 palettes
		ld a, [hli]
		ldh [c], a
	endr
	ret

.TransferMap:
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	and $f0
	ldh [rVDMA_SRC_LOW], a
	ld a, HIGH(vBGMap0)
	and $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, LOW(vBGMap0)
	ldh [rVDMA_DEST_LOW], a
	ld a, 2 * SCREEN_HEIGHT - 1
	ldh [rVDMA_LEN], a
	ret

Pokedex_VBlankAnimationFrontpicMap:
; Publish all seven rows containing the Selected frontpic from the persistent
; owner buffers. Both VRAM banks complete in one VBlank before BG0 is scanned.
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_MAP_PENDING_F, [hl]
	jr nz, .pending
	and a
	ret

.pending
	ldh a, [hBGMapUpdate]
	and a
	jr nz, .defer
	ldh a, [hDMATransfer]
	and a
	jr nz, .defer
	ldh a, [rLY]
	cp LY_VBLANK + 2
	jr nc, .defer

	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a

	ld a, BANK(vBGMap2)
	ldh [rVBK], a
	ld hl, wPokedexOwnerAttrmapBuffer + TILEMAP_WIDTH
	call .TransferRows
	xor a
	ldh [rVBK], a
	ld hl, wPokedexOwnerTilemapBuffer + TILEMAP_WIDTH
	call .TransferRows

	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ld hl, wPokedexAnimFlags
	res POKEDEX_ANIM_MAP_PENDING_F, [hl]
	xor a
	ldh [hVBlank], a
.defer
	scf
	ret

.TransferRows:
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	and $f0
	ldh [rVDMA_SRC_LOW], a
	ld a, HIGH(vBGMap0 + TILEMAP_WIDTH)
	and $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, LOW(vBGMap0 + TILEMAP_WIDTH)
	ldh [rVDMA_DEST_LOW], a
	ld a, 7 * TILEMAP_WIDTH / $10 - 1
	ldh [rVDMA_LEN], a
	ret

Pokedex_VBlankGridIconAnimation::
; A full-grid wrap publishes its portrait, palettes, and shadow OAM as one
; VBlank-owned transaction. Mainline code has already replaced each target
; grid row after its outgoing pixels passed.
	ld a, [wPokedexSelectedState]
	and a
	ret nz
	ld hl, wPokedexGridScrollFlags
	bit POKEDEX_GRID_SCROLL_COMMIT_F, [hl]
	jp nz, Pokedex_VBlankCommitWrappedGrid

; Both frames are resident. On a hardware-clock phase change, rewrite only
; the owned side-cell tile IDs and center-cell shadow OAM tile IDs.
	ldh a, [hBGMapUpdate]
	and a
	ret nz
	ldh a, [hCGBPalUpdate]
	and a
	ret nz
	ldh a, [hDMATransfer]
	and a
	ret nz
	ldh a, [hBGMapMode]
	and a
	ret nz
	ldh a, [hOAMUpdate]
	and a
	ret nz
	ldh a, [hVBlankCounter]
	inc a
	and 1 << POKEDEX_GRID_ICON_ANIM_FRAME_F
	ld b, a
	ld a, [wPokedexGridIconAnimFrame]
	cp b
	ret z
	ld a, b
	ld [wPokedexGridIconAnimFrame], a
	call Pokedex_UpdateCenterIconAnimationOAM

	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld a, 0
	lb bc, 0, 0
	ld de, vBGMap1 + 5 * TILEMAP_WIDTH + 1
	call Pokedex_VBlankUpdateSideCell
	ld a, 2
	lb bc, 0, 4
	ld de, vBGMap1 + 5 * TILEMAP_WIDTH + 9
	call Pokedex_VBlankUpdateSideCell
	ld a, 3
	lb bc, 1, 0
	ld de, vBGMap1 + 9 * TILEMAP_WIDTH + 1
	call Pokedex_VBlankUpdateSideCell
	ld a, 5
	lb bc, 1, 4
	ld de, vBGMap1 + 9 * TILEMAP_WIDTH + 9
	call Pokedex_VBlankUpdateSideCell
	ld a, 6
	lb bc, 2, 0
	ld de, vBGMap1 + 13 * TILEMAP_WIDTH + 1
	call Pokedex_VBlankUpdateSideCell
	ld a, 8
	lb bc, 2, 4
	ld de, vBGMap1 + 13 * TILEMAP_WIDTH + 9
	call Pokedex_VBlankUpdateSideCell

	pop af
	ldh [rVBK], a
	ret

Pokedex_VBlankCommitWrappedGrid:
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a

	ld a, [wPokedexGridScrollFlags]
	bit POKEDEX_GRID_SCROLL_SELECTION_F, a
	jr z, .palettes
	ld hl, wPokedexWRAM0Scratch
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	and $f0
	ldh [rVDMA_SRC_LOW], a
	ld a, HIGH(vTiles2)
	and $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, LOW(vTiles2)
	and $f0
	ldh [rVDMA_DEST_LOW], a
	ld a, 7 * 7 - 1
	ldh [rVDMA_LEN], a

.palettes
	ldh a, [hCGB]
	and a
	jp z, .oam
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals2)
	ldh [rWBK], a

	ld hl, wBGPals2 palette 1
	ld a, BGPI_AUTOINC palette 1
	ldh [rBGPI], a
	ld c, LOW(rBGPD)
	rept 7 palettes
		ld a, [hli]
		ldh [c], a
	endr

	ld hl, wOBPals2 palette 2
	ld a, OBPI_AUTOINC palette 2
	ldh [rOBPI], a
	ld c, LOW(rOBPD)
	rept 3 palettes
		ld a, [hli]
		ldh [c], a
	endr

	pop af
	ldh [rWBK], a

.oam
	call hTransferShadowOAM
	pop af
	ldh [rVBK], a
	ld hl, wPokedexGridScrollFlags
	res POKEDEX_GRID_SCROLL_COMMIT_F, [hl]
	ret

Pokedex_VBlankUpdateSideCell:
; a = visible grid index, b = visible row, c = side tile offset, de = BG map.
	ld l, a
	ld h, 0
	push de
	ld de, wPokedexGridFlags
	add hl, de
	pop de
	bit POKEDEX_GRID_CAUGHT_F, [hl]
	ret z

	ld a, [wPokedexGridTopPhysicalRow]
	add b
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .got_physical_row
	sub POKEDEX_GRID_CACHE_ROWS
.got_physical_row
	add a
	add a
	add a
	add c
	ld c, a
	ld a, [wPokedexGridIconAnimFrame]
	bit POKEDEX_GRID_ICON_ANIM_FRAME_F, a
	ld a, c
	jr z, .got_tile
	add POKEDEX_SIDE_ICON_FRAME1_TILE
.got_tile
	ld [de], a
	inc e
	inc a
	ld [de], a
	inc a
	ld c, a
	ld a, e
	add TILEMAP_WIDTH - 1
	ld e, a
	jr nc, .got_second_row
	inc d
.got_second_row
	ld a, c
	ld [de], a
	inc e
	inc a
	ld [de], a
	ret

Pokedex_CommitGridIconAnimationFrame:
; A selection change owns the hide-stage-reveal transaction. Once the old grid
; rows have passed, install all 24 side-column IDs for the synchronized phase;
; the caller releases the prepared center-column OAM and palette at VBlank.
	ldh a, [hCGB]
	and a
	ret z
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jr z, .copy

.wait_grid_end
	ldh a, [rLY]
	cp 144
	jr nc, .wait_next_frame
	cp 120
	jr c, .wait_grid_end
	di
	call .CopySideRows
	ei
	ret

.wait_next_frame
	ldh a, [rLY]
	cp 144
	jr nc, .wait_next_frame
	jr .wait_grid_end

.copy
	call .CopySideRows
	ret

.CopySideRows
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld hl, .SideTilemapCopies
	ld a, 2 * 2 * POKEDEX_GRID_HEIGHT
.next_row
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
	ld c, 2
.next_tile
.wait_vram
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait_vram
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .next_tile
	pop hl
	pop af
	dec a
	jr nz, .next_row
	pop af
	ldh [rVBK], a
	ret

.SideTilemapCopies:
	dw wTilemap +  5 * SCREEN_WIDTH + 1, vBGMap1 +  5 * TILEMAP_WIDTH + 1
	dw wTilemap +  6 * SCREEN_WIDTH + 1, vBGMap1 +  6 * TILEMAP_WIDTH + 1
	dw wTilemap +  5 * SCREEN_WIDTH + 9, vBGMap1 +  5 * TILEMAP_WIDTH + 9
	dw wTilemap +  6 * SCREEN_WIDTH + 9, vBGMap1 +  6 * TILEMAP_WIDTH + 9
	dw wTilemap +  9 * SCREEN_WIDTH + 1, vBGMap1 +  9 * TILEMAP_WIDTH + 1
	dw wTilemap + 10 * SCREEN_WIDTH + 1, vBGMap1 + 10 * TILEMAP_WIDTH + 1
	dw wTilemap +  9 * SCREEN_WIDTH + 9, vBGMap1 +  9 * TILEMAP_WIDTH + 9
	dw wTilemap + 10 * SCREEN_WIDTH + 9, vBGMap1 + 10 * TILEMAP_WIDTH + 9
	dw wTilemap + 13 * SCREEN_WIDTH + 1, vBGMap1 + 13 * TILEMAP_WIDTH + 1
	dw wTilemap + 14 * SCREEN_WIDTH + 1, vBGMap1 + 14 * TILEMAP_WIDTH + 1
	dw wTilemap + 13 * SCREEN_WIDTH + 9, vBGMap1 + 13 * TILEMAP_WIDTH + 9
	dw wTilemap + 14 * SCREEN_WIDTH + 9, vBGMap1 + 14 * TILEMAP_WIDTH + 9

Pokedex_UpdateCenterIconAnimationOAM:
	ld hl, wShadowOAMSprite00TileID
	xor a
	call .UpdateRow
	ld hl, wShadowOAMSprite04TileID
	ld a, 1
	call .UpdateRow
	ld hl, wShadowOAMSprite08TileID
	ld a, 2
	; fallthrough
.UpdateRow
	push hl
	call Pokedex_UpdateGridOAM.GetCenterIconTile
	pop hl
	ld de, OBJ_SIZE
	ld b, 4
.next_tile
	ld [hl], c
	inc c
	add hl, de
	dec b
	jr nz, .next_tile
	ret

Pokedex_UpdateGridOAM:
	call ClearSprites
	ld de, wShadowOAMSprite00
	xor a
	call .GetCenterIconTile
	ld a, 1
	ld b, 40
	ld l, OAM_BANK1 | 2
	call .PlaceCenterIcon
	ld de, wShadowOAMSprite04
	ld a, 1
	call .GetCenterIconTile
	ld a, 4
	ld b, 72
	ld l, OAM_BANK1 | 3
	call .PlaceCenterIcon
	ld de, wShadowOAMSprite08
	ld a, 2
	call .GetCenterIconTile
	ld a, 7
	ld b, 104
	ld l, OAM_BANK1 | 4
	call .PlaceCenterIcon

	ld de, wShadowOAMSprite12
	ld a, 0
	lb bc, 44, 64
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite13
	ld a, 1
	lb bc, 44, 96
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite14
	ld a, 2
	lb bc, 44, 128
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite15
	ld a, 3
	lb bc, 76, 64
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite16
	ld a, 4
	lb bc, 76, 96
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite17
	ld a, 5
	lb bc, 76, 128
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite18
	ld a, 6
	lb bc, 108, 64
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite19
	ld a, 7
	lb bc, 108, 96
	call .PlaceCaughtBall
	ld de, wShadowOAMSprite20
	ld a, 8
	lb bc, 108, 128
	call .PlaceCaughtBall

	ld de, wShadowOAMSprite21
	call .PlaceCursor
	call .GetScrollThumbY
	push af
	ld de, wShadowOAMSprite25
	pop af
	ld h, 54
	ld c, POKEDEX_SCROLL_THUMB_TILE
	ld l, 5
	jp .WriteOAM

.GetCenterIconTile:
; a = visible row; return c = first OBJ tile in its physical row.
	ld b, a
	ld a, [wPokedexGridTopPhysicalRow]
	add b
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .got_center_row
	sub POKEDEX_GRID_CACHE_ROWS
.got_center_row
	add a
	add a
	add a
	add POKEDEX_CENTER_ICON_TILE
	ld c, a
	push hl
	push de
	ld a, b
	add a
	add b
	inc a
	ld e, a
	ld d, 0
	ld hl, wPokedexGridFlags
	add hl, de
	bit POKEDEX_GRID_CAUGHT_F, [hl]
	jr z, .got_center_frame
	ld hl, wPokedexGridIconAnimFrame
	bit POKEDEX_GRID_ICON_ANIM_FRAME_F, [hl]
	jr z, .got_center_frame
	ld a, c
	add 4
	ld c, a
.got_center_frame
	pop de
	pop hl
	ret

.GetScrollThumbY:
; Scale the row-aligned offset over the 56-pixel scrollbar track.
	ld a, [wDexListingEnd + 1]
	and a
	jr nz, .scrollable
	ld a, [wDexListingEnd]
	cp POKEDEX_GRID_SIZE + 1
	jr c, .top
.scrollable
	ld a, [wDexListingEnd]
	ld e, a
	ld a, [wDexListingEnd + 1]
	ld d, a
	ld a, e
	add d ; 256 % 3 = 1
	jr nc, .reduce_remainder
	inc a
.reduce_remainder
	cp POKEDEX_GRID_WIDTH
	jr c, .got_remainder
	sub POKEDEX_GRID_WIDTH
	jr .reduce_remainder
.got_remainder
	ld c, a
	ld h, d
	ld l, e
	ld de, -POKEDEX_GRID_SIZE
	add hl, de
	ld a, c
	and a
	jr z, .got_max_offset
	cp 1
	ld de, 2
	jr z, .round_max_offset
	ld de, 1
.round_max_offset
	add hl, de
.got_max_offset
	ld d, h
	ld e, l ; de = maximum aligned top offset
	ld a, [wDexListingScrollOffset]
	ld c, a
	ld a, [wDexListingScrollOffset + 1]
	ld b, a ; bc = current aligned top offset
	ld h, d
	ld l, e
	srl h
	rr l ; round the final division to nearest
	xor a
	ld [wDexTempCounter], a
	ld a, 56
	ld [wDexTempCounter + 1], a
.scale_loop
	add hl, bc
	ld a, l
	sub e
	ld a, h
	sbc d
	jr c, .next_scale_step
	ld a, l
	sub e
	ld l, a
	ld a, h
	sbc d
	ld h, a
	ld a, [wDexTempCounter]
	inc a
	ld [wDexTempCounter], a
.next_scale_step
	ld a, [wDexTempCounter + 1]
	dec a
	ld [wDexTempCounter + 1], a
	jr nz, .scale_loop
	ld a, [wDexTempCounter]
	add 68
	ret
.top
	ld a, 68
	ret

.PlaceCenterIcon:
; a = grid position, b = screen y, c = first tile, l = attributes
	push hl
	push bc
	ld l, a
	ld h, 0
	ld bc, wPokedexGridFlags
	add hl, bc
	bit POKEDEX_GRID_SEEN_F, [hl]
	pop bc
	pop hl
	ret z
	ld a, b
	ld h, 104
	call .WriteOAM
	inc c
	ld a, b
	ld h, 112
	call .WriteOAM
	inc c
	ld a, b
	add 8
	ld h, 104
	call .WriteOAM
	inc c
	ld a, b
	add 8
	ld h, 112
	jp .WriteOAM

.PlaceCaughtBall:
; a = grid position, b = screen y, c = screen x
	push bc
	ld l, a
	ld h, 0
	ld bc, wPokedexGridFlags
	add hl, bc
	bit POKEDEX_GRID_CAUGHT_F, [hl]
	pop bc
	ret z
	ld h, c
	ld a, b
	ld c, POKEDEX_CAUGHT_BALL_TILE
	ld l, 1
	jp .WriteOAM

.PlaceCursor:
	ld a, [wDexListingCursor]
	add a
	ld c, a
	ld b, 0
	ld hl, .CursorPositions
	add hl, bc
	ld a, [hli]
	ld [wDexTempCounter], a
	ld a, [hl]
	ld [wDexTempCounter + 1], a

	ld h, a
	ld a, [wDexTempCounter]
	ld c, POKEDEX_LIST_CURSOR_TILE
	ld l, 0
	call .WriteOAM
	ld a, [wDexTempCounter + 1]
	add 20
	ld h, a
	ld a, [wDexTempCounter]
	ld l, OAM_XFLIP
	call .WriteOAM
	ld a, [wDexTempCounter + 1]
	ld h, a
	ld a, [wDexTempCounter]
	add 20
	ld l, OAM_YFLIP
	call .WriteOAM
	ld a, [wDexTempCounter + 1]
	add 20
	ld h, a
	ld a, [wDexTempCounter]
	add 20
	ld l, OAM_XFLIP | OAM_YFLIP
	jp .WriteOAM

.WriteOAM:
; a = screen y, h = screen x, c = tile, l = attributes
	add 16
	ld [de], a
	inc de
	ld a, h
	add 8
	ld [de], a
	inc de
	ld a, c
	ld [de], a
	inc de
	ld a, l
	ld [de], a
	inc de
	ret

.CursorPositions:
	db 34, 66
	db 34, 98
	db 34, 130
	db 66, 66
	db 66, 98
	db 66, 130
	db 98, 66
	db 98, 98
	db 98, 130

Pokedex_UpdateGridCursorOAM:
; Static page OAM occupies slots 0-20 and 25. Selection changes only rewrite
; the four cursor corners in slots 21-24.
	ld de, wShadowOAMSprite21
	jp Pokedex_UpdateGridOAM.PlaceCursor

DrawPokedexListWindow:
	hlcoord 0, 0
	lb bc, SCREEN_HEIGHT, 12
	ld a, $32
	call FillBoxWithByte
	hlcoord 0, 1
	lb bc, 2, 11
	call ClearBox
	ld a, $34
	hlcoord 0, 0
	ld bc, 11
	call ByteFill
	ld a, $6b
	ld [hl], a
	ld a, $6c
	hlcoord 11, 1
	ld b, 1
	call Pokedex_FillColumn2
	ld a, $6d
	hlcoord 0, 2
	ld bc, 11
	call ByteFill
	ld [hl], $6e
	ld a, $34
	hlcoord 0, 3
	ld bc, 11
	call ByteFill
	ld a, $6b
	ld [hl], a
	ld a, $6c
	hlcoord 11, 4
	ld b, 12
	call Pokedex_FillColumn2
	ld a, $39
	hlcoord 0, 16
	ld bc, 11
	call ByteFill
	ld a, $6b
	ld [hl], a
	ld a, $31
	hlcoord 0, 17
	ld bc, 12
	call ByteFill
	hlcoord 5, 3
	ld [hl], $3f
	inc hl
	ld [hl], $40
	hlcoord 5, 16
	ld [hl], $3f
	inc hl
	ld [hl], $40
	call .DrawAttrmap
	jp Pokedex_DrawListGrid

.DrawAttrmap:
	xor a
	hlcoord 0, 0, wAttrmap
	ld bc, SCREEN_AREA
	call ByteFill
	ld a, BG_YFLIP
	hlcoord 5, 16, wAttrmap
	ld [hli], a
	ld [hl], a
	hlcoord 11, 16, wAttrmap
	ld [hl], a
	ret

Pokedex_DrawListGrid:
	ld a, 0
	hlcoord 1, 5
	ld c, BG_BANK1 | 2
	call .PlaceGridEntry
	ld a, 1
	hlcoord 5, 5
	ld c, -1
	call .PlaceGridEntry
	ld a, 2
	hlcoord 9, 5
	ld c, BG_BANK1 | 3
	call .PlaceGridEntry
	ld a, 3
	hlcoord 1, 9
	ld c, BG_BANK1 | 4
	call .PlaceGridEntry
	ld a, 4
	hlcoord 5, 9
	ld c, -1
	call .PlaceGridEntry
	ld a, 5
	hlcoord 9, 9
	ld c, BG_BANK1 | 5
	call .PlaceGridEntry
	ld a, 6
	hlcoord 1, 13
	ld c, BG_BANK1 | 6
	call .PlaceGridEntry
	ld a, 7
	hlcoord 5, 13
	ld c, -1
	call .PlaceGridEntry
	ld a, 8
	hlcoord 9, 13
	ld c, BG_BANK1 | 7
	call .PlaceGridEntry
	ret

.PlaceGridEntry:
; a = visible position, c = side-icon attributes or -1 for the OAM column.
	ld [wDexTempCounter], a
	push bc
	push hl
	call .ClearGridCell
	pop hl
	ld a, [wDexTempCounter]
	ld e, a
	ld d, 0
	ld bc, wPokedexGridSpecies
	push hl
	ld h, d
	ld l, e
	add hl, bc
	ld a, [hl]
	pop hl
	and a
	jr z, .empty
	ld bc, wPokedexGridFlags
	push hl
	ld h, d
	ld l, e
	add hl, bc
	bit POKEDEX_GRID_SEEN_F, [hl]
	pop hl
	jr z, .unseen
	pop bc
	ld a, c
	cp -1
	ret z
	push bc
	push hl
	ld a, [wDexTempCounter]
	call .GetSideIconTile
	pop hl
	push hl
	call .PlaceGridTiles
	pop hl
	ld de, wAttrmap - wTilemap
	add hl, de
	pop bc
	ld a, c
	jp .FillGridCell

.unseen
	pop bc
	ld a, POKEDEX_UNSEEN_TILE
	jp .PlaceGridTiles

.empty
	pop bc
	ret

.ClearGridCell:
	push hl
	ld a, $32
	call .FillGridCell
	pop hl
	ld de, wAttrmap - wTilemap
	add hl, de
	xor a
	; fallthrough
.FillGridCell:
	ld [hli], a
	ld [hl], a
	ld de, SCREEN_WIDTH - 1
	add hl, de
	ld [hli], a
	ld [hl], a
	ret

.PlaceGridTiles:
	ld [hli], a
	inc a
	ld [hl], a
	ld de, SCREEN_WIDTH - 1
	add hl, de
	inc a
	ld [hli], a
	inc a
	ld [hl], a
	ret

.GetSideIconTile:
; a = visible position. Return the first BG tile for its physical side slot.
	ld b, 0
	cp POKEDEX_GRID_WIDTH
	jr c, .got_visible_row
	inc b
	sub POKEDEX_GRID_WIDTH
	cp POKEDEX_GRID_WIDTH
	jr c, .got_visible_row
	inc b
	sub POKEDEX_GRID_WIDTH
.got_visible_row
	ld c, a
	ld a, [wPokedexGridTopPhysicalRow]
	add b
	cp POKEDEX_GRID_CACHE_ROWS
	jr c, .got_physical_row
	sub POKEDEX_GRID_CACHE_ROWS
.got_physical_row
	add a
	add a
	add a
	ld b, a
	ld a, c
	and a
	ld a, b
	jr z, .got_frame0_tile
	add 4
.got_frame0_tile
	ld b, a
	ld a, [wDexTempCounter]
	ld e, a
	ld d, 0
	ld hl, wPokedexGridFlags
	add hl, de
	bit POKEDEX_GRID_CAUGHT_F, [hl]
	jr z, .use_frame0
	ld hl, wPokedexGridIconAnimFrame
	bit POKEDEX_GRID_ICON_ANIM_FRAME_F, [hl]
	jr z, .use_frame0
	ld a, b
	add POKEDEX_SIDE_ICON_FRAME1_TILE
	ret
.use_frame0
	ld a, b
	ret

DrawPokedexSearchResultsWindow:
	ld a, $34
	hlcoord 0, 0
	ld bc, 11
	call ByteFill
	ld a, $39
	hlcoord 0, 10
	ld bc, 11
	call ByteFill
	hlcoord 5, 0
	ld [hl], $3f
	hlcoord 5, 10
	ld [hl], $40
	hlcoord 11, 0
	ld [hl], $66
	ld a, $67
	hlcoord 11, 1
	ld b, SCREEN_HEIGHT / 2
	call Pokedex_FillColumn2
	ld [hl], $68
	ld a, $34
	hlcoord 0, 11
	ld bc, 11
	call ByteFill
	ld a, $39
	hlcoord 0, 17
	ld bc, 11
	call ByteFill
	hlcoord 11, 11
	ld [hl], $66
	ld a, $67
	hlcoord 11, 12
	ld b, 5
	call Pokedex_FillColumn2
	ld [hl], $68
	hlcoord 0, 12
	lb bc, 5, 11
	call ClearBox
	ld de, .esults_D
	hlcoord 0, 12
	call PlaceString
	ret

.esults_D
; (SEARCH R)
	db   "Esults"
	next ""
; (### FOUN)
	next "D!@"

DrawDexEntryScreenRightEdge:
	ldh a, [hBGMapAddress]
	ld l, a
	ldh a, [hBGMapAddress + 1]
	ld h, a
	push hl
	inc hl
	ld a, l
	ldh [hBGMapAddress], a
	ld a, h
	ldh [hBGMapAddress + 1], a
	hlcoord 19, 0
	ld [hl], $66
	hlcoord 19, 1
	ld a, $67
	ld b, 15
	call Pokedex_FillColumn2
	ld [hl], $68
	hlcoord 19, 17
	ld [hl], $3c
	xor a
	ld b, SCREEN_HEIGHT
	hlcoord 19, 0, wAttrmap
	call Pokedex_FillColumn2
	call WaitBGMap2
	pop hl
	ld a, l
	ldh [hBGMapAddress], a
	ld a, h
	ldh [hBGMapAddress + 1], a
	ret

Pokedex_FillColumn2:
; A local duplicate of Pokedex_FillColumn.
	push de
	ld de, SCREEN_WIDTH
.loop
	ld [hl], a
	add hl, de
	dec b
	jr nz, .loop
	pop de
	ret
