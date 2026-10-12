; Static Unown selection owns these existing Dex buffers exclusively.
; No animation job, picture cache, shared IRQ changes, or new RAM allocation.
ASSERT (wPokedexWRAM0Scratch & $f) == 0
ASSERT (wPokedexOwnerTilemapBuffer & $f) == 0
PokedexUnown_Publish:
; Mainline only: interrupts are enabled, Window hidden, BG0 owns the screen,
; BG updates are stopped, and no competing DMA/animation owner is active.
; The old hardware map remains visible while picture and software map stage.
; 49 picture + 36 map blocks fit in one VBlank, including normal-speed CGB.
; Arm at LY=143 so the normal IRQ cannot consume this VBlank first; start
; DMA at LY=144/145. A missed deadline retains the old whole frame.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a
	ld hl, wTilemap
	ld de, wPokedexOwnerTilemapBuffer
	ld b, SCREEN_HEIGHT
.row
REPT SCREEN_WIDTH
	ld a, [hli]
	ld [de], a
	inc de
ENDR
	ld a, e
	add TILEMAP_WIDTH - SCREEN_WIDTH
	ld e, a
	jr nc, .next
	inc d
.next
	dec b
	jr nz, .row
	ldh a, [rVBK]
	push af
.wait
	ldh a, [rLY]
	cp 143
	jr c, .wait
	cp 146
	jr nc, .wait
	di
.blank
	ldh a, [rLY]
	cp 144
	jr c, .blank
	cp 146
	jr c, .commit
	ei
	jr .wait
.commit
	xor a
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles2
	ld c, 7 * 7 - 1
	call .dma
	ld hl, wPokedexOwnerTilemapBuffer
	ld de, vBGMap0
	ld c, SCREEN_HEIGHT * TILEMAP_WIDTH / 16 - 1
	call .dma
.committed
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ei
	ret
.dma
	ld a, h
	ldh [rHDMA1], a
	ld a, l
	ldh [rHDMA2], a
	ld a, d
	ldh [rHDMA3], a
	ld a, e
	ldh [rHDMA4], a
	ld a, c ; Bit 7 clear: immediate, VBlank-only general-purpose DMA.
	ldh [rHDMA5], a
	ret
