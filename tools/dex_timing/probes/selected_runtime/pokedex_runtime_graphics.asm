; Selected-only runtime composition. Shared IRQs and portrait jobs are unchanged.
PokedexRuntime_LoadGlyph:
; A is a native font code; bank 3 is selected. Output is eight 1bpp rows.
	cp " "
	jr z, .blank
	cp '<LV>'
	jr z, .level
	cp $1c
	jr c, .font
	cp $1f
	jr nc, .font
	sub $1c
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, .Comparisons
	add hl, de
	ld de, wPokedexRuntimeGlyph
	ld bc, 8
	jp CopyBytes
.blank
	xor a
	ld hl, wPokedexRuntimeGlyph
	ld bc, 8
	jp ByteFill
.level
	ld hl, FontBattleExtra + 14 tiles
	ld de, wPokedexRuntimeTile
	ld bc, TILE_SIZE
	ld a, BANK(FontBattleExtra)
	call FarCopyBytes
	ld hl, wPokedexRuntimeTile
	ld de, wPokedexRuntimeGlyph
	ld b, 8
.level_row
	ld a, [hli]
	or [hl]
	inc hl
	ld [de], a
	inc de
	dec b
	jr nz, .level_row
	ret
.font
	sub $80
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, Font
	add hl, de
	ld de, wPokedexRuntimeGlyph
	ld bc, 8
	ld a, BANK(Font)
	jp FarCopyBytes
.Comparisons
	db 0, 64, 32, 16, 32, 64, 0, 0
	db 0, 16, 32, 64, 32, 16, 0, 0
	db 0, 0, 112, 0, 112, 0, 0, 0

PokedexRuntime_NormalTile:
; A=previous glyph, B=current glyph, C=phase 1/5. No stored text bitmap.
	ld [wPokedexRuntimePreviousChar], a
	ld a, b
	ld [wPokedexRuntimeGlyph], a
	ld a, c
	ld [wPokedexRuntimePhase], a
	farcall PokedexRuntime_FontPair
	ret

PokedexRuntime_LoadTitles:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexRuntimeTile)
	ldh [rSVBK], a
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld hl, PokedexRuntime_StatsText
	ld de, PokedexInfoStatsTitle
	call PokedexRuntime_LoadTitleWord
	ld hl, PokedexRuntime_EvolutionsText
	ld de, PokedexInfoEvolutionsTitle
	call PokedexRuntime_LoadTitleWord
IF !DEF(DEX_RUNTIME_SEMANTIC)
	call PokedexRuntime_BuildParents
ENDC
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ret
PokedexRuntime_LoadTitleWord:
	ld a, " "
	ld [wPokedexRuntimePreviousChar], a
.letter
	ld a, [de]
	cp "@"
	ret z
	inc de
	push de
	ld e, a
	ld d, 0
	ld a, e
	xor $80
	ld e, a
	ld d, 0
	push hl
	ld hl, vTiles1
	add hl, de
	; Signed font IDs are converted to sixteen-byte physical offsets.
	pop hl
	ld a, [hli]
	cp "@"
	jr nz, .character
	dec hl
	ld a, " "
.character
	ld b, a
	ld a, [wPokedexRuntimePreviousChar]
	push hl
	push bc
	ld c, 5
	call PokedexRuntime_NormalTile
	pop bc
	ld a, b
	ld [wPokedexRuntimePreviousChar], a
	pop hl
	pop de
	push hl
	push de
	dec de
	ld a, [de]
	xor $80
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, vTiles1
	add hl, de
	ld d, h
	ld e, l
	ld hl, wPokedexRuntimeTile
	ld bc, TILE_SIZE
IF DEF(DEX_RUNTIME_ANCESTORS)
	call PokedexAncestors_CopyTitleTile
ELSE
	call CopyBytes
ENDC
	pop de
	pop hl
	jr .letter
PokedexRuntime_StatsText: db "Stats@"
PokedexRuntime_EvolutionsText: db "Evolutions@"
IF DEF(DEX_RUNTIME_ANCESTORS)
PokedexRuntime_AncestorsText: db "Evolves from@"
ENDC

PokedexInfoStatsTitle:
	db $ca, $cb, $cc, $cd, $ce, $cf, "@"
PokedexInfoEvolutionsTitle:
	db $d7, $d8, $d9, $da, $db, $dc, $dd, $de, $e4, $e5, $cf, "@"
IF DEF(DEX_RUNTIME_ANCESTORS)
PokedexInfoEvolvesFromTitle:
	db $b5, $b6, $b7, $b8, $b9, $ba, $bb, $bc, $bd, $be, $bf, $c0, $c1, "@"
ENDC

PokedexRuntime_CopyTiles:
; Runtime output already occupies GFX. Only atlas B needs a retained RAM copy.
IF DEF(DEX_RUNTIME_RESTORE_ROM)
	jp PokedexRuntime_CopyROMTiles
ELIF DEF(DEX_RUNTIME_RESTORE_VRAM)
	ld a, [wPokedexRuntimeReturnRepair]
	and a
	jr z, .ready
	ld a, [wPokedexInfoCopyTile]
	ld c, a
	ld a, [wPokedexInfoTileCount]
	sub c
	jr z, .ready
	cp 9
	jr c, .count
	ld a, 8
.count
	push af
	ld l, c
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	push hl
	ld de, wPokedexInfoGFX
	add hl, de
	ld d, h
	ld e, l
	pop hl
	ld bc, vTiles5
	add hl, bc
	pop af
	push af
	add a
	add a
	add a
	ld b, a ; pairs of bytes
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
.pair
	; Mode 0/1 has at least the next 80-dot mode 2 before VRAM locks.
	; Two reads finish within that margin even at normal CPU speed. DI
	; prevents an interrupt from invalidating the sampled STAT window.
	di
.wait_vram
	ldh a, [rSTAT]
	and 2
	jr nz, .wait_vram
	ld a, [hli]
	ld [de], a
	inc de
	ld a, [hli]
	ld [de], a
	inc de
	ei
	dec b
	jr nz, .pair
	pop af
	ldh [rVBK], a
	pop bc
	ld a, [wPokedexInfoCopyTile]
	add b
	ld [wPokedexInfoCopyTile], a
	ret
.ready
	ld a, [wPokedexInfoTileCount]
	ld [wPokedexInfoCopyTile], a
	ld a, POKEDEX_INFO_UPLOAD
	ld [wPokedexInfoState], a
	ret
ELSE
	ld a, [wPokedexRuntimeReturnRepair]
	and a
	jr nz, .copy
	ld a, [wPokedexInfoAtlasBuffer]
	and a
	jr nz, .copy
	ld a, [wPokedexInfoTileCount]
	ld [wPokedexInfoCopyTile], a
	jr .ready
.copy
	ld a, [wPokedexInfoCopyTile]
	ld c, a
	ld a, [wPokedexInfoTileCount]
	sub c
	jr z, .ready
	cp 9
	jr c, .count
	ld a, 8
.count
	ld [wPokedexRuntimeNumberTile], a
	ld h, 0
	ld l, c
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	push hl
	ld a, [wPokedexRuntimeReturnRepair]
	and a
	jr nz, .repair
	ld de, wPokedexInfoGFX
	add hl, de
	ld de, POKEDEX_ANIM_PAYLOAD
	call .length
	call CopyBytes
	pop hl
	ld de, wPokedexRuntimeVisibleBGFX
	add hl, de
	ld d, h
	ld e, l
	ld hl, POKEDEX_ANIM_PAYLOAD
	call .length
	ld a, BANK(wPokedexRuntimeVisibleBGFX)
	ldh [rSVBK], a
	call CopyBytes
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	jr .copied
.repair
	ld de, wPokedexRuntimeVisibleBGFX
	add hl, de
	ld de, POKEDEX_ANIM_PAYLOAD
	call .length
	ld a, BANK(wPokedexRuntimeVisibleBGFX)
	ldh [rSVBK], a
	call CopyBytes
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	pop hl
	ld de, wPokedexInfoGFX
	add hl, de
	ld d, h
	ld e, l
	ld hl, POKEDEX_ANIM_PAYLOAD
	call .length
	call CopyBytes
.copied
	ld a, [wPokedexRuntimeNumberTile]
	ld b, a
	ld a, [wPokedexInfoCopyTile]
	add b
	ld [wPokedexInfoCopyTile], a
	ret
.ready
	ld a, POKEDEX_INFO_UPLOAD
	ld [wPokedexInfoState], a
	ret
.length
	ld a, [wPokedexRuntimeNumberTile]
	swap a
	ld c, a
	ld b, 0
	ret
ENDC

PokedexRuntime_GFXAddress:
; A = tile number.
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wPokedexInfoGFX
	add hl, de
	ret

PokedexRuntime_StoreTile:
	call PokedexRuntime_GFXAddress
	ld d, h
	ld e, l
	ld hl, wPokedexRuntimeTile
	ld bc, TILE_SIZE
	jp CopyBytes

PokedexRuntime_NewTile:
; A hash narrows candidates; byte comparison makes hash collisions harmless.
	ld hl, wPokedexRuntimeTile
	ld b, TILE_SIZE
	ld de, 0
.hash
	ld a, [hli]
	ld c, a
	add e
	ld e, a
	ld a, d
	rlca
	xor c
	ld d, a
	dec b
	jr nz, .hash
	ld a, e
	ld [wPokedexRuntimeHash], a
	ld a, d
	ld [wPokedexRuntimeHash + 1], a
	ld hl, wPokedexInfoTileSources
	ld c, 0
.find
	ld a, [wPokedexInfoTileCount]
	cp c
	jr z, .new
	ld a, [hli]
	cp e
	ld a, [hli]
	jr nz, .next
	cp d
	jr nz, .next
	push hl
	push bc
	push de
	ld a, c
	call PokedexRuntime_GFXAddress
	ld de, wPokedexRuntimeTile
	ld b, TILE_SIZE
.compare
	ld a, [de]
	cp [hl]
	jr nz, .different
	inc de
	inc hl
	dec b
	jr nz, .compare
	pop de
	pop bc
	pop hl
	ld a, c
	jp PokedexInfo_ExistingTile
.different
	pop de
	pop bc
	pop hl
.next
	inc c
	jr .find
.new
	ld a, e
	ld [hli], a
	ld [hl], d
	ld a, c
	push af
	call PokedexRuntime_StoreTile
	ld hl, wPokedexInfoTileCount
	inc [hl]
	pop af
	jp PokedexInfo_ExistingTile

PokedexRuntime_BuildShared:
	call PokedexRuntime_BuildSharedOne
	ld a, [wPokedexInfoTileCount]
	cp POKEDEX_INFO_SHARED_TILES
	ret nc
	jp PokedexRuntime_BuildSharedOne

PokedexRuntime_BuildSharedOne:
; At most two small label/bar tiles per admitted step.
	ld a, [wPokedexInfoTileCount]
	cp 10
	jr nc, .bar
	ld e, a
	ld d, 0
	ld hl, .LabelChars
	add hl, de
	ld b, [hl]
	ld a, " "
	ld c, 1
	call PokedexRuntime_NormalTile
	jr .store
.bar
	sub 10
	ld e, a
	ld d, 0
	ld hl, .BarWidths
	add hl, de
	ld a, [hl]
	call PokedexRuntime_BarTile
.store
	ld a, [wPokedexInfoTileCount]
	call PokedexRuntime_StoreTile
	ld a, [wPokedexInfoTileCount]
	call PokedexRuntime_GFXAddress
	ld d, h
	ld e, l
	ld a, [wPokedexInfoTileCount]
	add a
	ld l, a
	ld h, 0
	ld bc, wPokedexInfoTileSources
	add hl, bc
	ld [hl], e
	inc hl
	ld [hl], d
	ld hl, wPokedexInfoTileCount
	inc [hl]
	ret
.LabelChars db "HPAtkDefSp"
.BarWidths db 1, 3, 5, 7, 8

PokedexRuntime_BarTile:
; A=terminal pixels; the original editable bar sheet remains authoritative.
	ld [wPokedexRuntimeBarWidth], a
	cp 8
	jr z, .full
	srl a
	add 4
	jr .source
.full
	ld a, 8
.source
	sub 3 ; the source sheet's unused tiles 1..3 are not linked
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, PokedexRuntimeBarGFX
	add hl, de
	ld de, wPokedexRuntimeTile
	ld bc, TILE_SIZE
	ld a, BANK(PokedexRuntimeBarGFX)
	call FarCopyBytes
	ld hl, wPokedexRuntimeTile
	ld b, TILE_SIZE
	ld a, [wPokedexRuntimeBarWidth]
	cp 8
	jr z, .invert
	ld c, a
	ld a, $ff
.mask
	srl a
	dec c
	jr nz, .mask
	ld c, a
.partial
	ld a, [hl]
	cpl
	add a
	or c
	ld [hli], a
	dec b
	jr nz, .partial
	ret
.invert
	ld a, [hl]
	cpl
	ld [hli], a
	dec b
	jr nz, .invert
	ret

PokedexRuntime_BuildNumbers:
	call PokedexRuntime_StartNumbers
.loop
	call PokedexRuntime_NumberStep
	ld a, [wPokedexRuntimeNumberTile]
	cp 4
	jr c, .loop
	ret

PokedexRuntime_StartNumbers:
	ld a, [wPokedexInfoScratch]
	ld b, "0" - 1
.hundreds
	inc b
	sub 100
	jr nc, .hundreds
	add 100
	ld c, a
	ld a, b
	cp "0"
	jr nz, .hundred_set
	ld a, " "
.hundred_set
	ld [wPokedexRuntimeDigits], a
	ld a, c
	ld b, "0" - 1
.tens
	inc b
	sub 10
	jr nc, .tens
	add 10
	add "0"
	ld [wPokedexRuntimeDigits + 2], a
	ld a, b
	cp "0"
	jr nz, .ten_set
	ld a, [wPokedexRuntimeDigits]
	cp " "
	ld a, b
	jr nz, .ten_set
	ld a, " "
.ten_set
	ld [wPokedexRuntimeDigits + 1], a
	xor a
	ld [wPokedexRuntimeNumberTile], a
	ret

PokedexRuntime_NumberStep:
	call PokedexRuntime_NumberTile
	ld a, [wPokedexRuntimeNumberTile]
	cp 4
	ret nc
	jp PokedexRuntime_NumberTile

PokedexRuntime_NumberTile:
	ld a, [wPokedexRuntimeNumberTile]
	ld c, a
	ld a, " "
	ld b, a
	ld a, c
	cp 3
	jr z, .previous
	ld l, a
	ld h, 0
	ld de, wPokedexRuntimeDigits
	add hl, de
	ld b, [hl]
.previous
	ld a, c
	and a
	ld a, " "
	jr z, .compose
	ld a, c
	dec a
	ld l, a
	ld h, 0
	ld de, wPokedexRuntimeDigits
	add hl, de
	ld a, [hl]
.compose
	ld c, 5
	call PokedexRuntime_NormalTile
	ld a, [wPokedexRuntimeNumberTile]
	cp 3
	call z, PokedexRuntime_NumberBar
	ld a, [wPokedexRuntimeNumberTile]
	ld c, a
	ld a, [wPokedexInfoTileCount]
	add c
	push af
	call PokedexRuntime_StoreTile
	pop af
	call PokedexRuntime_GFXAddress
	ld d, h
	ld e, l
	ld a, [wPokedexRuntimeNumberTile]
	add a
	ld l, a
	ld h, 0
	ld bc, wPokedexRuntimeNumberSources
	add hl, bc
	ld [hl], e
	inc hl
	ld [hl], d
	ld hl, wPokedexRuntimeNumberTile
	inc [hl]
	ld a, [hl]
	cp 4
	ret c
	ld a, [wPokedexInfoState]
	cp POKEDEX_INFO_RUNTIME_NUMBER
	ret nz
	jp PokedexInfo_PlanStats.numbers

PokedexRuntime_NumberBar:
	ld hl, wPokedexRuntimeTile
	ld b, 8
.background
	inc hl
	ld a, [hld]
	ld [hli], a
	inc hl
	dec b
	jr nz, .background
	ld a, [wPokedexInfoWidth]
	and a
	ret z
	cp 2
	ld c, 7
	ld hl, PokedexRuntimeBarGFX + 6 tiles
	jr nz, .source
	ld c, 6
	ld hl, PokedexRuntimeBarGFX
.source
	ld a, c
	ld [wPokedexRuntimeBarMask], a
	ld de, wPokedexRuntimePreviousGlyph
	ld bc, TILE_SIZE
	ld a, BANK(PokedexRuntimeBarGFX)
	call FarCopyBytes
	ld hl, wPokedexRuntimeTile
	ld de, wPokedexRuntimePreviousGlyph
	ld b, TILE_SIZE
.combine
	ld a, [wPokedexRuntimeBarMask]
	ld c, a
	cpl
	and [hl]
	push af
	ld a, [de]
	inc de
	cpl
	swap a
	rra
	and c
	ld c, a
	pop af
	or c
	ld [hli], a
	dec b
	jr nz, .combine
	ret

PokedexInfoLabelTiles:
	db 0, 1, 255
	db 2, 3, 4
	db 5, 6, 7
	db 8, 9, 2
	db 8, 9, 5
	db 8, 9, 6

PokedexRuntime_LoadLevelMarker:
; LCD-off Dex startup; the original battle glyph is the sole source.
	ld hl, FontBattleExtra + 14 tiles
	ld de, POKEDEX_ANIM_PAYLOAD
	ld bc, TILE_SIZE
	ld a, BANK(FontBattleExtra)
	call FarCopyBytes
	ld hl, POKEDEX_ANIM_PAYLOAD
	ld de, vTiles2 tile $7d
	ld b, 8
.row
	ld a, [hli]
	or [hl]
	inc hl
	cpl
	ld c, a
	xor a
	ld [de], a
	inc de
	ld a, c
	ld [de], a
	inc de
	dec b
	jr nz, .row
	ret

PokedexRuntime_StartText:
	call PokedexRuntime_ExpandContractions
	ld hl, wPokedexRuntimeTextBuffer
	ld b, 0
.length
	ld a, [hli]
	cp "@"
	jr z, .mode
	inc b
	jr .length
.mode
	ld a, b
	cp 16
	ld a, 0
	jr c, .normal
	inc a
.normal
	ld [wPokedexRuntimeTextCompact], a
	xor a
	ld [wPokedexRuntimeTextReady], a
	ld [wPokedexRuntimeTextTile], a
	ld hl, wPokedexRuntimeLine
	ld bc, 16 * 8
	call ByteFill
	ld a, LOW(wPokedexRuntimeTextBuffer)
	ld [wPokedexRuntimeTextSource], a
	ld a, HIGH(wPokedexRuntimeTextBuffer)
	ld [wPokedexRuntimeTextSource + 1], a
	ld a, 5
	ld [wPokedexRuntimeTextX], a
	ld a, 2
	ld [wPokedexRuntimeTextState], a
	ret

PokedexRuntime_ExpandContractions:
; Source names encode apostrophe pairs as one glyph; preserve the old layout.
	ld hl, wPokedexRuntimeTextBuffer
	ld de, wPokedexRuntimeLine
	ld bc, 32
	call CopyBytes
	ld hl, wPokedexRuntimeLine
	ld de, wPokedexRuntimeTextBuffer
.character
	ld a, [hli]
	cp $d0
	jr c, .copy
	cp $d7
	jr nc, .copy
	sub $d0
	push hl
	ld l, a
	ld h, 0
	ld bc, .Suffixes
	add hl, bc
	ld c, [hl]
	pop hl
	ld a, "'"
	ld [de], a
	inc de
	ld a, c
.copy
	ld [de], a
	inc de
	cp "@"
	jr nz, .character
	ret
.Suffixes db "dlmrstv"

PokedexRuntime_TextGlyphStep:
; One native glyph is packed into the temporary 128px line per admitted step.
	ld a, [wPokedexRuntimeTextSource]
	ld l, a
	ld a, [wPokedexRuntimeTextSource + 1]
	ld h, a
	ld a, [hli]
	cp "@"
	jp z, .done
	push af
	ld a, l
	ld [wPokedexRuntimeTextSource], a
	ld a, h
	ld [wPokedexRuntimeTextSource + 1], a
	pop af
	call PokedexRuntime_LoadGlyph
	xor a
	ld [wPokedexRuntimeGlyphMin], a
	ld a, 8
	ld [wPokedexRuntimeGlyphWidth], a
	ld a, [wPokedexRuntimeTextCompact]
	and a
	jr z, .draw
	ld hl, wPokedexRuntimeGlyph
	ld b, 8
	xor a
.ink
	or [hl]
	inc hl
	dec b
	jr nz, .ink
	and a
	jr nz, .bounds
	ld a, 3 ; blank contributes four columns, without an extra ink separator
	ld [wPokedexRuntimeGlyphWidth], a
	jr .draw
.bounds
	ld c, a
	ld b, 0
.minimum
	bit 7, a
	jr nz, .min_done
	add a
	inc b
	jr .minimum
.min_done
	ld a, b
	ld [wPokedexRuntimeGlyphMin], a
	ld a, 8
	sub b
	ld b, a
.maximum
	bit 0, c
	jr nz, .width
	srl c
	dec b
	jr .maximum
.width
	ld a, b
	ld [wPokedexRuntimeGlyphWidth], a
.draw
	ld a, [wPokedexRuntimeTextX]
	srl a
	srl a
	srl a
	ld l, a
	ld h, 0
	ld de, wPokedexRuntimeLine
	add hl, de
	ld a, l
	ld [wPokedexRuntimeDrawPointer], a
	ld a, h
	ld [wPokedexRuntimeDrawPointer + 1], a
	xor a
	ld [wPokedexRuntimeGlyphRow], a
.row
	ld a, [wPokedexRuntimeGlyphRow]
	ld l, a
	ld h, 0
	ld de, wPokedexRuntimeGlyph
	add hl, de
	ld b, [hl]
	ld a, [wPokedexRuntimeGlyphMin]
	ld c, a
	and a
	jr z, .cropped
.crop
	sla b
	dec c
	jr nz, .crop
.cropped
	ld a, b
	ld [wPokedexRuntimeBits], a
	ld a, [wPokedexRuntimeTextX]
	and 7
	ld c, a
	jr z, .left_ready
.left
	srl b
	dec c
	jr nz, .left
.left_ready
	ld a, [wPokedexRuntimeDrawPointer]
	ld l, a
	ld a, [wPokedexRuntimeDrawPointer + 1]
	ld h, a
	ld a, b
	or [hl]
	ld [hli], a
	ld a, [wPokedexRuntimeTextX]
	and 7
	jr z, .next_row
	ld c, a
	ld a, 8
	sub c
	ld c, a
	ld a, [wPokedexRuntimeBits]
.right
	add a
	dec c
	jr nz, .right
	or [hl]
	ld [hl], a
.next_row
	ld de, 15
	add hl, de
	ld a, l
	ld [wPokedexRuntimeDrawPointer], a
	ld a, h
	ld [wPokedexRuntimeDrawPointer + 1], a
	ld hl, wPokedexRuntimeGlyphRow
	inc [hl]
	ld a, [hl]
	cp 8
	jp c, .row
	ld a, [wPokedexRuntimeTextCompact]
	and a
	ld a, 8
	jr z, .advance
	ld a, [wPokedexRuntimeGlyphWidth]
	inc a
.advance
	ld hl, wPokedexRuntimeTextX
	add [hl]
	ld [hl], a
	ret
.done
	ld a, [wPokedexRuntimeTextX]
	add 7
	srl a
	srl a
	srl a
	ld [wPokedexRuntimeTextTiles], a
	ld a, 3
	ld [wPokedexRuntimeTextState], a
	ret

PokedexRuntime_TextTileStep:
	ld a, [wPokedexRuntimeTextTile]
	ld l, a
	ld h, 0
	ld de, wPokedexRuntimeLine
	add hl, de
	ld de, wPokedexRuntimeTile
	ld b, 8
.row
	xor a
	ld [de], a
	inc de
	ld a, [hl]
	cpl
	ld [de], a
	inc de
	ld a, l
	add 16
	ld l, a
	jr nc, .next
	inc h
.next
	dec b
	jr nz, .row
	call PokedexInfo_NewTile
	ld hl, wPokedexRuntimeTextTile
	inc [hl]
	ld a, [wPokedexRuntimeTextTiles]
	cp [hl]
	ret nz
	xor a
	ld [wPokedexRuntimeTextState], a
	scf
	ret
