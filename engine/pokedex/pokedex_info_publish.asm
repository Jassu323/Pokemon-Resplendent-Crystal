; Interrupt-owned lower-panel publication. Included in the existing bank $77
; dispatcher, so no ISR FarCall scratch or new fixed-bank bridge is required.

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

Pokedex_VBlankInfo:
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_INFO
	jp nz, .idle
	ld a, [wPokedexSelectedState]
	cp DEXSELECT_STATE_ACTIVE
	jr nz, .idle
	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld a, [wPokedexOwnerTransition]
	cp POKEDEX_OWNER_TRANSITION_INFO
	jr nz, .animate
	ld a, [wPokedexAnimSchedulerControl]
	bit POKEDEX_ANIM_UPLOAD_ACTIVE_F, a
	jr nz, .done
	ldh a, [rLY]
	cp LY_VBLANK
	jr c, .done
	cp LY_VBLANK + 3
	jr nc, .done
	call Pokedex_VBlankInfoAssets
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexOwnerAttrmapBuffer + 9 * TILEMAP_WIDTH
	call Pokedex_InfoTransferLowerRows
	xor a
	ldh [rVBK], a
	ld hl, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
	call Pokedex_InfoTransferLowerRows
	ld a, [wPokedexOwnerTilemapBuffer + 8 * TILEMAP_WIDTH + 2]
	ld [vBGMap0 + 8 * TILEMAP_WIDTH + 2], a
	ld a, BANK(wBGPals2)
	ldh [rSVBK], a
	ld a, OBPI_AUTOINC palette 2
	ldh [rOBPI], a
	ld hl, wOBPals2 palette 2
	ld c, LOW(rOBPD)
	ld b, 2 palettes
	call Pokedex_InfoCopyHardwarePalette
	call hTransferShadowOAM
	xor a
	ld [wPokedexOwnerTransition], a
	jr .done
.animate
	; A tiny OAM-only update can follow portrait publication; it does not
	; need the much earlier admission boundary used by map publication.
	ldh a, [rLY]
	cp LY_VBLANK
	jr nc, .animate_now
	cp 52 ; the first type-badge sprite is scanned at y=56
	jr nc, .done
.animate_now
	call Pokedex_InfoAnimateMinis
.done
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ld hl, wPokedexAnimFlags
	bit POKEDEX_ANIM_MAP_PENDING_F, [hl]
	jr nz, .keep_request
	ldh a, [hVBlank]
	and 1 << VBLANK_DEX_QUIET_F
	ldh [hVBlank], a
.keep_request
	scf
	ret
.idle
	and a
	ret

Pokedex_VBlankInfoAssets:
; Bank 3 already selected. Mainline has uploaded the inactive atlas and minis.
	ld a, [wPokedexInfoState]
	cp POKEDEX_INFO_READY
	jr nz, .not_info
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_INFO
	jr nz, .not_info
	ld a, TRUE
	ld [wPokedexInfoVisible], a
.oam
	ld a, [wPokedexInfoAtlasBuffer]
	ld [wPokedexInfoActiveAtlasBuffer], a
	ld a, [wPokedexInfoMiniCount]
	ld [wPokedexInfoActiveMiniCount], a
	ld a, [wPokedexInfoMiniBuffer]
	ld [wPokedexInfoActiveMiniBuffer], a
	xor a
	ld [wPokedexInfoMiniPhase], a
	ld [wPokedexInfoState], a
	ret
.not_info
	xor a
	ld [wPokedexInfoVisible], a
	ret

Pokedex_InfoAnimateMinis:
	ld a, [wPokedexInfoActiveMiniCount]
	and a
	ret z
	ldh a, [hVBlankCounter]
	inc a
	and 8
	ld b, a
	ld a, [wPokedexInfoMiniPhase]
	cp b
	ret z
	ld a, b
	ld [wPokedexInfoMiniPhase], a
	srl a
	ld c, a ; tile phase 0 or 4
	ld a, [wPokedexInfoActiveMiniBuffer]
	and a
	ld a, POKEDEX_INFO_MINI_OBJ_TILE
	jr z, .base
	add 16
.base
	add c
	ld hl, wShadowOAMSprite08TileID
	ld b, 4
.first
	ld [hl], a
	inc a
	ld de, 4
	add hl, de
	dec b
	jr nz, .first
	ld c, a
	ld a, [wPokedexInfoActiveMiniCount]
	cp 2
	jr c, .dma
	ld a, c
	add 4
	ld b, 4
.second
	ld [hl], a
	inc a
	ld de, 4
	add hl, de
	dec b
	jr nz, .second
.dma
	jp hTransferShadowOAM

Pokedex_InfoTransferLowerRows:
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	ldh [rVDMA_SRC_LOW], a
	ld a, HIGH(vBGMap0 + 9 * TILEMAP_WIDTH) & $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, LOW(vBGMap0 + 9 * TILEMAP_WIDTH)
	ldh [rVDMA_DEST_LOW], a
	ld a, 7 * TILEMAP_WIDTH / $10 - 1
	ldh [rVDMA_LEN], a
	ret

Pokedex_InfoCopyHardwarePalette:
.wait
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .wait
	ld a, [hli]
	ldh [c], a
	dec b
	jr nz, .wait
	ret

PokedexInfoHPEndpointGFX:
; Color 0 transparency, 1 border, 2 fill. Visible width is one or two pixels.
	db 0,0, $80,0, $80,0, $80,0, $80,0, $80,0, $80,0, 0,0
	db 0,0, $c0,0, $40,$80, $40,$80, $40,$80, $40,$80, $c0,0, 0,0
