; Shares the pointer/padding helpers' bank, but has no shared executed path.
ASSERT BANK(PokedexUnown_PreparePicture) == BANK(GetFrontpicPointer)
ASSERT BANK(PokedexUnown_PreparePicture) == BANK(PadFrontpic)
PokedexUnown_PreparePicture:
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	; GetBaseData consumes wCurSpecies, not wCurPartySpecies.
	call GetBaseData
	ldh a, [rSVBK]
	push af
	ld a, [wBasePicSize]
	and $f
	push af
	call GetFrontpicPointer
	inc hl ; Skip the full animation dictionary count.
	ld a, BANK(wDecompressScratch)
	ldh [rSVBK], a
	ld a, b
	ld de, wDecompressScratch
	call FarDecompress
	pop bc ; Native square dimension in B.
	ld hl, wPokedexWRAM0Scratch
	ld de, wDecompressScratch
	call PadFrontpic
	pop af
	ldh [rSVBK], a
	ret
