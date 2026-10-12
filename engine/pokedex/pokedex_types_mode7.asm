; The Type owner cooperatively services HBlank without changing shared IRQs.

PokedexTypes_CacheChart:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoGFX)
	ldh [rSVBK], a
	ld hl, TypeMatchups
	ld de, wPokedexInfoGFX
	ld bc, TypeMatchupsEnd - TypeMatchups
	ld a, BANK(TypeMatchups)
	call FarCopyBytes
	pop af
	ldh [rSVBK], a
	ret

PokedexTypes_PrepareLower:
IF DEF(TYPE_PANEL_PRECOMPUTED)
	call PokedexTypes_LoadRecord
ELSE
	call PokedexTypes_DrawSelection
ENDC
	; Only the five lower rows changed. Do not restage the upper frame.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexOwnerTilemapBuffer)
	ldh [rSVBK], a
	hlcoord 0, 12
	ld de, wPokedexOwnerTilemapBuffer + 12 * TILEMAP_WIDTH
	ld c, ' '
	call .map
	hlcoord 0, 12, wAttrmap
	ld de, wPokedexOwnerAttrmapBuffer + 12 * TILEMAP_WIDTH
	ld c, 0
	call .map
	pop af
	ldh [rSVBK], a
	ret
.map
	ld b, 5
.row
	push bc
	ld b, SCREEN_WIDTH
.cell
	call PokedexTypes_Yield
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .cell
	ld b, TILEMAP_WIDTH - SCREEN_WIDTH
	ld a, c
.pad
	ld [de], a
	inc de
	dec b
	jr nz, .pad
	pop bc
	dec b
	jr nz, .row
	ret

PokedexTypes_Fill:
	push de
	ld d, a
.byte
	call PokedexTypes_Yield
	ld a, d
	ld [hli], a
	dec bc
	ld a, b
	or c
	jr nz, .byte
	ld a, d
	pop de
	ret

PokedexTypes_VBlank::
	ld hl, hVBlankCounter
	inc [hl]
	ldh a, [rDIV]
	ld b, a
	ldh a, [hRandomAdd]
	adc b
	ldh [hRandomAdd], a
	ldh a, [rDIV]
	ld b, a
	ldh a, [hRandomSub]
	sbc b
	ldh [hRandomSub], a
	ld a, [TYPES_EXIT]
	and a
	jr nz, .exit
	ld a, [TYPES_PENDING]
	and a
	jr z, .no_publication
	call PokedexTypes_CommitLower
	ld a, [TYPES_PAGE]
	ldh [hLYOverrideStart], a
	xor a
	ld [TYPES_PENDING], a
	ldh [hOAMUpdate], a
.no_publication
	ldh a, [hOAMUpdate]
	and a
	call z, hTransferShadowOAM
	ldh a, [hLYOverrideStart]
	ld h, a
	ld l, 8
	call PokedexTypes_WriteAccents
	xor a
	ld [TYPES_EVENT], a
	ld a, 21
	ld [TYPES_NEXT_LINE], a
	jr .bookkeeping
.exit
	ld hl, .Gray
	ld b, 4
	ld d, $80 | 8
.mask_palette
	ld a, d
	ldh [rBCPS], a
	ld c, 8
.mask_color
	ld a, [hli]
	ldh [rBCPD], a
	dec c
	jr nz, .mask_color
	ld hl, .Gray
	ld a, d
	add 8
	ld d, a
	dec b
	jr nz, .mask_palette
	xor a
	ld [TYPES_ACTIVE], a
	ldh [hVBlank], a
	ldh [hLCDCPointer], a
	ldh [hLYOverrideStart], a
.bookkeeping
	xor a
	ld [wVBlankOccurred], a
	ld a, [wOverworldDelay]
	and a
	jr z, .text_delay
	dec a
	ld [wOverworldDelay], a
.text_delay
	ld a, [wTextDelayFrames]
	and a
	jr z, .input
	dec a
	ld [wTextDelayFrames], a
.input
	call UpdateJoypad
	call PokedexTypes_UpdateSound
	ldh a, [hSeconds]
	ldh [hUnusedBackup], a
	ld a, TRUE
	ld [TYPES_FRAME_READY], a
	ret
.Gray
	RGB 5,5,5, 5,5,5, 5,5,5, 5,5,5

PokedexTypes_Yield::
	push af
	ld a, [TYPES_ACTIVE]
	and a
	jr z, .done
	ld a, [TYPES_NEXT_LINE]
	cp $ff
	jr z, .done
	push bc
	push de
	push hl
	ld b, a
	sub 4
	ld c, a
	ldh a, [rLY]
	cp c
	jr c, .restore
	cp 144
	jr nc, .restore
.line
	ldh a, [rLY]
	cp b
	jr c, .line
.hblank
	ldh a, [rSTAT]
	and 3
	jr nz, .hblank
	ld a, [TYPES_EVENT]
	add a
	add a
	add a
	add 16
	ld l, a
	ldh a, [hLYOverrideStart]
	ld h, a
	call PokedexTypes_WriteAccents
	ld hl, TYPES_EVENT
	inc [hl]
	ld e, [hl]
	ld d, 0
	ld hl, .Lines
	add hl, de
	ld a, [hl]
	ld [TYPES_NEXT_LINE], a
.restore
	pop hl
	pop de
	pop bc
.done
	pop af
	ret
.Lines
	db 21, 35, 49, 63, 77, 95, 103, 111, 119, 127, $ff

PokedexTypes_WriteAccents::
	ld c, LOW(rBCPD)
FOR palette_id, 1, 5
	ld a, $80 | palette_id * 8 + 4
	ldh [rBCPS], a
	ld a, [hli]
	ldh [c], a
	ld a, [hli]
	ldh [c], a
ENDR
	ret

IF DEF(TYPE_PANEL_PRECOMPUTED)
PokedexTypes_LoadRecord:
	ld a, [TYPES_CURSOR]
	add a
	ld e, a
	ld d, 0
	ld hl, PokedexTypes_PanelPointers
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	push hl
	ld a, [hli]
	ld [TYPES_I_COUNT], a
	ld a, [hli]
	ld [TYPES_W_COUNT], a
	ld a, [hli]
	ld [TYPES_R_COUNT], a
	ld a, [hli]
	ld [TYPES_R_ROW], a
	ld de, TYPES_W_LIST
	ld a, [TYPES_W_COUNT]
	ld c, a
	ld b, 0
	call .copy
	ld de, TYPES_R_LIST
	ld a, [TYPES_R_COUNT]
	ld c, a
	ld b, 0
	call .copy
	ld de, TYPES_I_LIST
	ld a, [TYPES_I_COUNT]
	ld c, a
	ld b, 0
	call .copy
	pop hl
	ld de, 22
	add hl, de
	decoord 0, 12
	ld bc, 100
	call .copy
	decoord 0, 12, wAttrmap
	ld bc, 100
	call .copy
	ld a, [TYPES_PAGE]
	ld d, a
	ld e, 56
	ld bc, 40
	call .copy
	ldh a, [hLYOverrideStart]
	ld h, a
	ld l, 8
	ld a, [TYPES_PAGE]
	ld d, a
	ld e, 8
	ld bc, 48
	call .copy
	jp PokedexTypes_DrawSelection.Cursor
.copy
	ld a, b
	or c
	ret z
.byte
	call PokedexTypes_Yield
	ld a, [hli]
	ld [de], a
	inc de
	dec bc
	ld a, b
	or c
	jr nz, .byte
	ret

INCLUDE "engine/pokedex/pokedex_types_mode7_records.asm"
ENDC
