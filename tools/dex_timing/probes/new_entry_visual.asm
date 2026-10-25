NewDexEntry_VisualLayout::
; Registration owns temporary graphics SRAM, not the live battle WRAM0 overlay.
	ldh a, [hCGB]
	and a
	jr nz, .cgb
	ld b, SCGB_POKEDEX
	call GetSGBLayout
	farcall Pokedex_ApplyUsualPals
	ret
.cgb
	farcall CGB_PokedexBuildSelectedMonLayout
	hlcoord 18, 1, wAttrmap
	ld a, POKEDEX_DESCRIPTION_FOOTPRINT_PAL
	ld [hli], a
	ld [hl], a
	hlcoord 18, 2, wAttrmap
	ld [hli], a
	ld [hl], a
	ld a, 3
	ld [wAttrmap + 17 * SCREEN_WIDTH + 18], a
	call NewDexEntry_RedFooterPalette
	farcall Pokedex_SetDescriptionTypeAttrsAndPals
	ld a, [wPokedexSelectedSpecies]
	push af
	ld a, [wCurPartySpecies]
	ld [wPokedexSelectedSpecies], a
	farcall PokedexInfo_StageTypePalettes
	pop af
	ld [wPokedexSelectedSpecies], a
	call NewDexEntry_LoadTypeBadges
	farcall CGB_PokedexApplyLayout
	farcall Pokedex_ApplyUsualPals
	ret

NewDexEntry_RedFooterPalette:
; The cursor keeps the UI foreground colors, but its font background is red.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rSVBK], a
	ld hl, wBGPals1
	ld de, wBGPals1 palette 3
	ld bc, 1 palettes
	call CopyBytes
	ld a, [wBGPals1 + 1 colors]
	ld [wBGPals1 palette 3 + 3 colors], a
	ld a, [wBGPals1 + 1 colors + 1]
	ld [wBGPals1 palette 3 + 3 colors + 1], a
	pop af
	ldh [rSVBK], a
	ret

NewDexEntry_LoadTypeBadges:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wBaseType1)
	ldh [rSVBK], a
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ld a, BANK(sNewDexEntryUploadBuffer)
	call OpenSRAM
	ld a, [wBaseType1]
	ld c, a
	ld de, sNewDexEntryUploadBuffer
	farcall PokedexInfo_CopyCompactTypeTilesByC
	ld a, [wBaseType1]
	ld b, a
	ld a, [wBaseType2]
	cp b
	ld c, 4
	jr z, .upload
	ld c, a
	ld de, sNewDexEntryUploadBuffer + 4 tiles
	farcall PokedexInfo_CopyCompactTypeTilesByC
	ld c, 8
.upload
	push bc
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld hl, vTiles3 tile POKEDEX_TYPE_OBJ_TILE
	ld de, sNewDexEntryUploadBuffer
	call NewDexEntry_Get2bpp
	pop af
	ldh [rVBK], a
	call CloseSRAM
	pop bc
	ld hl, wShadowOAMSprite00
	ld b, POKEDEX_TYPE_OBJ_TILE
	ld d, 75
	ld e, OAM_BANK1
.sprite
	ld a, 72
	ld [hli], a
	ld a, d
	ld [hli], a
	ld a, b
	ld [hli], a
	ld a, e
	ld [hli], a
	inc b
	ld a, d
	add 8
	ld d, a
	ld a, b
	and 3
	jr nz, .next
	ld d, 115
	inc e
.next
	dec c
	jr nz, .sprite
	ld a, b
	cp POKEDEX_TYPE_OBJ_TILE + 8
	jr z, .done
	xor a
	ld bc, 4 * 4
	call ByteFill
.done
	pop af
	ldh [rSVBK], a
	ret
