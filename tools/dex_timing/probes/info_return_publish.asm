; PRIVATE PREFLIGHT ONLY. Existing bank-$77 dispatcher, no fixed-bank bridge.
Pokedex_VBlankInfoReturn:
	ld a, [wPokedexOwnerTransition]
	cp POKEDEX_OWNER_TRANSITION_INFO_RETURN
	jr nz, .not_ours
	ldh a, [hBGMapUpdate]
	and a
	jr nz, .pending
	ldh a, [hDMATransfer]
	and a
	jr nz, .pending
	ldh a, [rLY]
	cp LY_VBLANK
	jr c, .pending
	cp LY_VBLANK + 3
	jr nc, .pending
	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a
	xor a
	ldh [rVBK], a
	ld hl, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
	call Pokedex_InfoTransferLowerRows
.published
	xor a
	ld [wPokedexInfoActiveAtlasBuffer], a
	ld [wPokedexOwnerTransition], a
	ldh [hVBlank], a
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
.pending
	scf
	ret
.not_ours
	and a
	ret
