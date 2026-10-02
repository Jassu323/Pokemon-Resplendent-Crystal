; PRIVATE DIAGNOSTIC PREFLIGHT. Never included by production builds.
; One byte is borrowed from the unused persistent end of the Dex map union.
DEF PrototypeIconDestination EQU wPokedexWRAM0ScratchEnd - 1
ASSERT PrototypeIconDestination >= wPokedexWRAM0Scratch + $510

SECTION "Private icon destination helpers", ROMX[$7b00], BANK[$77]
PrototypeIconBank77Start:
PrototypeSelectiveMask:
	ld a, [wPokedexSelectedState]
	cp 2
	jr z, .portrait
	ld a, B_Pokedex_BlackOutBG
	ld hl, Pokedex_BlackOutBG
	rst FarCall
	ret
.portrait
	ldh a, [rSVBK]
	push af
	ld a, B_wBGPals1
	ldh [rSVBK], a
	ld hl, wBGPals1 + 8
	ld b, 4
.white
	ld a, $ff
	ld [hli], a
	ld a, $7f
	ld [hli], a
	dec b
	jr nz, .white
	pop af
	ldh [rSVBK], a
	ret

PrototypeFootprintDestination:
	ld de, $8b10
	ldh a, [hCGB]
	and a
	ret z
	ld a, [wPokedexSelectedState]
	cp 2
	jr z, .selected
	cp 4
	ret nz
.selected
	ld a, [PrototypeIconDestination]
	and a
	ret z
	ld de, $96c0
	ret

PrototypeFootprintResidentSpecies:
; Zero invalidates the original slot's cache tag without marking the visible
; alternate footprint absent ($ff). A temporary species ID could be recycled.
	push de
	call PrototypeFootprintDestination
	ld a, d
	cp $96
	pop de
	ld a, [wCurPartySpecies]
	ret nz
	xor a
	ret
PrototypeReloadNormalFootprint:
; Only Description re-entry repairs use this path. The original Listing
; transfer helper remains byte-for-byte unchanged in its full ROMX bank.
	ld a, [wPokedexSelectedSpecies]
	ld [wTempSpecies], a
	ld a, B_Pokedex_PrepareCurrentFootprint
	ld hl, Pokedex_PrepareCurrentFootprint
	rst FarCall
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch + $310
	ld de, $8b10
	ld c, 4
	call Pokedex_HDMATransferCacheGFX
	pop af
	ldh [rVBK], a
	ld a, [wPokedexSelectedSpecies]
	ld [wPokedexResidentFootprintSpecies], a
	ret

PrototypeReturnToListing:
; The currently visible Description uses the alternate footprint, while the
; Listing does not display one. Restore its normal slot before cache reuse.
	call Pokedex_NormalizeListingAfterSelectedMon
	ldh a, [hCGB]
	and a
	ret z
	ld a, [PrototypeIconDestination]
	and a
	ret z
	jp PrototypeReloadNormalFootprint
PrototypeIconBank77End:

SECTION "Private icon placement helpers", ROMX[$7b00], BANK[$a0]
PrototypeIconBankA0Start:
PrototypeInitializeIcons:
	xor a
	ld [PrototypeIconDestination], a
	jp LowVolume

PrototypeBeginInternalIcons:
; Read the outgoing backing before StageDescription replaces it. No VRAM read.
	ld a, [wTilemap + 20 + 18]
	cp $b1
	ld a, 0
	jr nz, .store
	inc a
.store
	ld [PrototypeIconDestination], a
	jp PokedexSelectedMon_BeginWarmTransition

PrototypeDrawDescriptionFootprint:
	ldh a, [hCGB]
	and a
	jr nz, .cgb
	ld a, B_Pokedex_DrawResidentFootprint
	ld hl, Pokedex_DrawResidentFootprint
	rst FarCall
	ret
.cgb
	ld a, [PrototypeIconDestination]
	and a
	jr nz, .alternate
; Listing returns retain the base frontpic, but may leave the normal footprint
; slot owned by an older species after the Description used its alternate slot.
	ld a, [wPokedexSelectedSpecies]
	ld b, a
	ld a, [wPokedexResidentFootprintSpecies]
	cp b
	jr z, .original
	ld a, $77
	ld hl, PrototypeReloadNormalFootprint
	rst FarCall
.original
	ld a, $b1
	jr .place
.alternate
	ld a, $6c
.place
	ld hl, wTilemap + 20 + 18
	ld [hli], a
	inc a
	ld [hl], a
	inc a
	ld hl, wTilemap + 40 + 18
	ld [hli], a
	inc a
	ld [hl], a
	ret

PrototypeTypeDestination:
	ld de, $9640
	ld a, [PrototypeIconDestination]
	and a
	ret z
	ld de, $9700
	ret

PrototypeTypeBase:
	ld a, [PrototypeIconDestination]
	and a
	ld a, $64
	ret z
	ld a, $70
	ret

PrototypePlaceTypes:
	call PrototypeTypeBase
	ld hl, wTilemap + 7 * 20 + 9
	call Pokedex_LoadDescriptionTypeGFX_PlaceType
	ld a, [wBaseType1]
	ld b, a
	ld a, [wBaseType2]
	cp b
	ret z
	call PrototypeTypeBase
	add 4
	ld hl, wTilemap + 7 * 20 + 14
	jp Pokedex_LoadDescriptionTypeGFX_PlaceType
PrototypeIconBankA0End:
