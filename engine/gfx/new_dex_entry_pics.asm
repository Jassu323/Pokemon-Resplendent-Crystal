SECTION "New Dex Entry Pics", ROMX

ASSERT BANK(NewDexEntry_LoadAnimatedFrontpic) == BANK(_PrepareFrontpic)

NewDexEntry_LoadAnimatedFrontpic::
; Only registration uses the batched uploader. Keep GetAnimatedFrontpic and
; its other callers unchanged, including battle and the Stats Screen.
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call IsAPokemon
	ret c
	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	xor a
	ldh [hBGMapMode], a
	ldh [rVBK], a
	ld a, BANK(sEnemyFrontPicTileCount)
	call OpenSRAM
	ld de, vTiles2
	push de
	call _PrepareFrontpic
	pop hl
	push hl
	ld de, sPaddedEnemyFrontPic
	ld c, 7 * 7
	call NewDexEntry_Get2bpp
	pop hl
	ld a, 1
	ldh [rVBK], a
	push hl
	ld de, sPaddedEnemyFrontPic
	ld c, 7 * 7
	call NewDexEntry_Get2bpp
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
	ld a, [sEnemyFrontPicTileCount]
	sub c
	jr z, .done
	ld c, a
	push hl
	push bc
	call LoadFrontpicTiles
	pop bc
	pop hl
	ld de, wDecompressScratch
	ld a, c
	sub 128 - 7 * 7
	jr c, .tail
; Preserve the legacy resident layout: tile $7f remains blank.
	inc a
	ld [sEnemyFrontPicTileCount], a
	ld c, 127 - 7 * 7
	call NewDexEntry_Get2bpp
	ld de, wDecompressScratch + (127 - 7 * 7) tiles
	ld hl, vTiles4
	ld a, [sEnemyFrontPicTileCount]
	ld c, a
.tail
	ldh a, [hROMBank]
	ld b, a
	call NewDexEntry_Get2bpp
.done
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	jp CloseSRAM
