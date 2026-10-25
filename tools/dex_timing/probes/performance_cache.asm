; PRIVATE PROTOTYPE. Restore borrowed frame 0 before reusing complete row tags.
; The outgoing Info panel has already moved to atlas A. No input or icon
; animation can run during this synchronous hidden owner restoration.
PokedexPerf_RepairFrame0:
	xor a
	ld [wPokedexGridPendingPhysicalRow], a
.row
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld l, a
	ld h, 0
	ld de, wPokedexGridCacheRowOffsets
	add hl, de
	ld a, [hli]
	ld [wPokedexGridPendingRowOffset], a
	ld e, a
	ld a, [hl]
	ld [wPokedexGridPendingRowOffset + 1], a
	ld d, a
	ld hl, POKEDEX_GRID_SIDE_FRAME0_GFX
	ld bc, 8 tiles
	xor a
	call ByteFill
	ld a, d
	and e
	inc a
	jr z, .upload
	xor a
	ld [wDexTempCounter], a
.icon
	ld hl, wPokedexGridPendingRowOffset
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, [wDexTempCounter]
	add e
	ld e, a
	jr nc, .source
	inc d
.source
	call Pokedex_PrepareGridCacheRow.GetSeenSpeciesAtOffset
	jr z, .next_icon
	ld c, a
	farcall ReadMonMenuIconForPokedex
	ld h, d
	ld l, e
	ld de, POKEDEX_GRID_SIDE_FRAME0_GFX
	push af
	ld a, [wDexTempCounter]
	and a
	jr z, .copy
	ld de, POKEDEX_GRID_SIDE_FRAME0_GFX + 4 tiles
.copy
	pop af
	ld a, b
	ld bc, 4 tiles
	call FarCopyBytes
.next_icon
	ld a, [wDexTempCounter]
	and a
	jr nz, .upload
	ld a, 2
	ld [wDexTempCounter], a
	jr .icon
.upload
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld a, [wPokedexGridPendingPhysicalRow]
	add a
	ld l, a
	ld h, 0
	ld de, Pokedex_UploadPendingGridCacheRow.SideFrame0RowDestinations
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ld hl, POKEDEX_GRID_SIDE_FRAME0_GFX
	ld c, 8
	call Pokedex_HDMATransferCacheGFX
	pop af
	ldh [rVBK], a
	ld hl, wPokedexGridPendingPhysicalRow
	inc [hl]
	ld a, [hl]
	cp POKEDEX_GRID_CACHE_ROWS
	jp nz, .row
	ret
