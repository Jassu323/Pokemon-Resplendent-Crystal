; INVESTIGATION ONLY: private ROM overlay, never included by the game build.
; Compare a request-free palette stage, one-VBlank publication, and late hide.

SECTION "Private transition staging", ROMX[$76e5], BANK[$a0]

PrototypeStagePals:
; ApplyPals already copied the identity ($e4) BG mapping. Preserve the usual
; OBJ0 conversion and register values without queuing a hardware publication.
	ld a, $e4
	ldh [rBGP], a
	ld a, $e0
	ldh [rOBP0], a
	ldh a, [rSVBK]
	push af
	ld a, 5
	ldh [rSVBK], a
	ld hl, wOBPals2
	ld de, wOBPals1
	ld b, $e0
	ld c, 1
	call CopyPals
	pop af
	ldh [rSVBK], a
	ret

PrototypePrepareThenHide:
	ld a, B_Pokedex_PrepareSelectedMonTiles
	ld hl, Pokedex_PrepareSelectedMonTiles
	rst FarCall
	call PokedexSelectedMon_BeginHiddenTransition
	ld a, B_Pokedex_CommitPreparedSelectedMonGFX
	ld hl, Pokedex_CommitPreparedSelectedMonGFX
	rst FarCall
	ret

PrototypeAlreadyRevealed:
	ldh a, [hCGB]
	and a
	ret nz
	jp PokedexSelectedMon_Reveal

PrototypeStagingEnd:

SECTION "Private transition publication", ROMX[$74e5], BANK[$77]

PrototypeCopyBacking:
	ldh a, [hCGB]
	and a
	jp z, Pokedex_CopyBackingToBG
	ld a, [wPokedexSelectedState]
	cp 2
	jp nz, Pokedex_CopyBackingToBG
.wait
	ldh a, [rLY]
	cp 143
	jr nz, .wait
	di
.wait_vblank
	ldh a, [rLY]
	cp 144
	jr c, .wait_vblank
	cp 145
	jp nc, PrototypeRetry
PrototypeCommit:
	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	ld a, 3
	ldh [rSVBK], a
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexOwnerAttrmapBuffer
	call PrototypeTransferMap
	xor a
	ldh [rVBK], a
	ld hl, wPokedexOwnerTilemapBuffer
	call PrototypeTransferMap
	ld a, 5
	ldh [rSVBK], a
	ld a, $80
	ldh [rBGPI], a
	ld hl, wBGPals2
	ld c, LOW(rBGPD)
	rept 64
		ld a, [hli]
		ldh [c], a
	endr
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	xor a
	ldh [hCGBPalUpdate], a
	ld [wPokedexSelectedBGPaletteDirty], a
	ld [wPokedexSelectedOBJPaletteDirty], a
PrototypeCommitted:
	ei
	ret
PrototypeRetry:
	ei
	jp PrototypeCopyBacking.wait
PrototypeTransferMap:
	ld a, h
	ldh [rHDMA1], a
	ld a, l
	ldh [rHDMA2], a
	ld a, $18
	ldh [rHDMA3], a
	xor a
	ldh [rHDMA4], a
	ld a, 35
	ldh [rHDMA5], a
	ret

PrototypePublicationEnd:
