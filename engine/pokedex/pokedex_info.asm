; Selected Dex lower-panel owner. See docs/pokedex_info.md.
; Font composition and evolution traversal are build-time work, not playback.

PokedexInfo_LoadTitleGFX:
; Dex startup has the LCD off. These sixteen cells are unused font gaps.
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld de, PokedexInfoTitleGFX
	ld hl, vTiles1 tile $4a
	lb bc, BANK(PokedexInfoTitleGFX), 6
	call Get2bpp
	ld de, PokedexInfoTitleGFX + 6 tiles
	ld hl, vTiles1 tile $57
	lb bc, BANK(PokedexInfoTitleGFX), 8
	call Get2bpp
	ld de, PokedexInfoTitleGFX + 14 tiles
	ld hl, vTiles1 tile $64
	lb bc, BANK(PokedexInfoTitleGFX), 2
	call Get2bpp
	pop af
	ldh [rVBK], a
	ret

PokedexInfo_Reset:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld hl, wPokedexInfoState
	ld bc, wPokedexInfoWorkspaceEnd - wPokedexInfoState
	xor a
	call ByteFill
	pop af
	ldh [rSVBK], a
	ret

PokedexInfo_Cancel:
	ld a, [wPokedexOwnerTransition]
	cp POKEDEX_OWNER_TRANSITION_INFO
	jr nz, .state
	xor a
	ld [wPokedexOwnerTransition], a
.state
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	xor a
	ld [wPokedexInfoState], a
	ld [wPokedexMovesState], a
	ld [wPokedexInfoActiveMiniCount], a
	pop af
	ldh [rSVBK], a
	ret

PokedexInfo_ReturnDescription:
	call PokedexInfo_Cancel
	xor a
	ld [wPokedexSelectedView], a
	ld [wPokedexDescriptionPage], a
	ld [wPokedexStatus], a
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoRestoreDescription)
	ldh [rSVBK], a
	ld a, 1
	ld [wPokedexInfoRestoreDescription], a
	ld hl, wPokedexOwnerAttrmapBuffer + 8 * TILEMAP_WIDTH
	ld bc, 8 * TILEMAP_WIDTH
	xor a
	call ByteFill
	ld hl, wPokedexOwnerTilemapBuffer + 15 * TILEMAP_WIDTH + 1
	ld bc, 19
	ld a, $32
	call ByteFill
	ld hl, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH + 3
	ld bc, 17
	call ByteFill
	; Info's half-tile-shifted labels occupy the otherwise blank text gutter.
FOR row, 10, 15
	ld [wPokedexOwnerTilemapBuffer + row * TILEMAP_WIDTH + 1], a
ENDR
	ld a, [wPokedexInfoCaught]
	and a
	jr nz, .restored
	ld [wPokedexInfoPage], a
	call PokedexInfo_DrawBadge
	ld a, POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT
	ld [wPokedexOwnerTransition], a
	ldh a, [hVBlank]
	or VBLANK_POKEDEX
	ldh [hVBlank], a
.restored
	pop af
	ldh [rSVBK], a
	ret

PokedexInfo_Activate:
	ldh a, [hCGB]
	and a
	ret z
	call PokedexInfo_Cancel
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_INFO
	jr nz, .first
	ld a, [wPokedexInfoPage]
	inc a
	ld hl, wPokedexInfoPageCount
	cp [hl]
	jr c, .page
.first
	xor a
.page
	ld [wPokedexInfoPage], a
	ld a, DEXSELECT_VIEW_INFO
	ld [wPokedexSelectedView], a
	ld a, POKEDEX_INFO_INITIALIZE
	ld [wPokedexInfoState], a
	pop af
	ldh [rSVBK], a
	ret

PokedexInfo_PrepareInitial:
; No animation or cry is running during species-owner preparation.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	xor a
	ld [wPokedexInfoPage], a
	call PokedexInfo_Initialize
.build
	call PokedexInfo_Step
	ld a, [wPokedexInfoState]
	cp POKEDEX_INFO_READY
	jr nz, .build
	call PokedexInfo_StagePalettes
	call PokedexInfo_StageOAM
	pop af
	ldh [rSVBK], a
	ret

PokedexInfo_Service:
	ldh a, [hCGB]
	and a
	ret z
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld a, [wPokedexOwnerTransition]
	cp POKEDEX_OWNER_TRANSITION_INFO
	jr z, .request
	ld a, [wPokedexInfoActiveMiniCount]
	and a
	jr z, .job
.request
	ldh a, [hVBlank]
	or VBLANK_POKEDEX
	ldh [hVBlank], a
.job
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_INFO
	jr nz, .done
	ld a, [wPokedexOwnerTransition]
	and a
	jr nz, .done
	ld b, POKEDEX_INFO_SERVICE_SLICES
.slice
	ld a, [wPokedexInfoState]
	and a
	jr z, .done
	ld a, [wPokedexAnimPlaybackState]
	cp POKEDEX_ANIM_PLAYBACK_PLAYING
	jr nz, .admit
	ldh a, [hVBlankCounter]
	ld hl, wPokedexAnimLoopTick
	cp [hl]
	jr nz, .done
	ldh a, [rLY]
	cp POKEDEX_INFO_LATEST_LY
	jr nc, .done
.admit
	ld a, [wPokedexInfoState]
	cp POKEDEX_INFO_READY
	jr z, .publish
	push bc
	call PokedexInfo_Step
	pop bc
	dec b
	jr nz, .slice
	jr .done
.publish
	call PokedexInfo_StagePalettes
	di
	call PokedexInfo_StageOAM
	ld a, POKEDEX_OWNER_TRANSITION_INFO
	ld [wPokedexOwnerTransition], a
	ldh a, [hVBlank]
	or VBLANK_POKEDEX
	ldh [hVBlank], a
	ei
.done
	pop af
	ldh [rSVBK], a
	ret

PokedexInfo_Initialize:
; Caller has bank 3 selected. Stable species indexes own the generated graph.
	xor a
	ld [wPokedexInfoRow], a
	ld [wPokedexInfoTileCount], a
	ld [wPokedexInfoCopyTile], a
	ld [wPokedexInfoUploadTile], a
	ld [wPokedexInfoMiniCount], a
	ld [wPokedexInfoRestoreDescription], a
	ld [wPokedexInfoLineRemaining], a
	ld a, [wPokedexInfoActiveAtlasBuffer]
	xor 1
	ld [wPokedexInfoAtlasBuffer], a
	xor a
	ld hl, wPokedexInfoOAM
	ld bc, 32
	call ByteFill
	ld a, [wPokedexInfoActiveMiniBuffer]
	xor 1
	ld [wPokedexInfoMiniBuffer], a
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
	ld de, PokedexInfoSpecies
	add hl, de
	inc hl
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [wPokedexInfoPage]
	and a
	jr z, .list
	dec a
	add a
	add a
	ld e, a
	ld d, 0
	add hl, de
.list
	ld a, l
	ld [wPokedexInfoEvolutionList], a
	ld a, h
	ld [wPokedexInfoEvolutionList + 1], a
	ld a, POKEDEX_INFO_CLEAR
	ld [wPokedexInfoState], a
	ret

PokedexInfo_PrepareSpecies:
; Cache immutable page data before the selected portrait or cry begins.
	ldh a, [rSVBK]
	push af
	ld a, [wPokedexSelectedSpecies]
	ld c, a
	ld a, BANK(wPokedexCaught)
	ldh [rSVBK], a
	ld a, c
	call CheckCaughtMon
	ld a, 0
	jr z, .caught
	inc a
.caught
	ld c, a
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld a, c
	ld [wPokedexInfoCaught], a
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
	ld de, PokedexInfoSpecies
	add hl, de
	ld a, [hli]
	inc a
	srl a
	inc a
	ld [wPokedexInfoPageCount], a
	ld de, wPokedexInfoStats
	ld hl, .BaseStatAddresses
	ld b, 6
.stat
	push hl
	push bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, BANK(wBaseHP)
	call GetFarWRAMByte
	ld [de], a
	inc de
	pop bc
	pop hl
	inc hl
	inc hl
	dec b
	jr nz, .stat
	pop af
	ldh [rSVBK], a
	ret
.BaseStatAddresses:
	dw wBaseHP, wBaseAttack, wBaseDefense, wBaseSpecialAttack, wBaseSpecialDefense, wBaseSpeed

PokedexInfo_Step:
	ld a, [wPokedexInfoState]
	cp POKEDEX_INFO_INITIALIZE
	jp z, PokedexInfo_Initialize
	cp POKEDEX_INFO_CLEAR
	jp z, PokedexInfo_ClearRow
	cp POKEDEX_INFO_COPY
	jp z, PokedexInfo_CopyTiles
	cp POKEDEX_INFO_UPLOAD
	jp z, PokedexInfo_UploadTiles
	cp POKEDEX_INFO_MINI_UPLOAD
	jp z, PokedexInfo_UploadMini
	cp POKEDEX_INFO_RECORD
	jp z, PokedexInfo_RecordPage
	cp POKEDEX_INFO_PLAN
	ret nz
	ld a, [wPokedexInfoCaught]
	and a
	jr z, .ready
	ld a, [wPokedexInfoPage]
	and a
	jp z, PokedexInfo_PlanStats
	jp PokedexInfo_PlanEvolution
.ready
	jp PokedexInfo_BeginRecord

PokedexInfo_ClearRow:
	ld a, [wPokedexInfoRow]
	add 8
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wPokedexOwnerTilemapBuffer
	add hl, de
	ld bc, 32
	ld a, $32
	call ByteFill
	ld de, -32
	add hl, de
	ld [hl], $36
	push hl
	ld de, SCREEN_WIDTH
	add hl, de
	ld [hl], $67
	pop hl
	ld de, wPokedexOwnerAttrmapBuffer - wPokedexOwnerTilemapBuffer
	add hl, de
	ld bc, 32
	xor a
	call ByteFill
	ld hl, wPokedexInfoRow
	inc [hl]
	ld a, [hl]
	cp 8
	ret c
; Divider and badge upper row remain the shell's real pixels.
	ld hl, PokedexDescriptionTilemap + 8 * SCREEN_WIDTH
	ld de, wPokedexOwnerTilemapBuffer + 8 * TILEMAP_WIDTH
	ld bc, SCREEN_WIDTH
	ld a, BANK(PokedexDescriptionTilemap)
	call FarCopyBytes
	ld a, $76
	ld [wPokedexOwnerTilemapBuffer + 8 * TILEMAP_WIDTH + 20], a
	xor a
	ld [wPokedexInfoRow], a
	call PokedexInfo_DrawBadge
	ld a, [wPokedexInfoCaught]
	and a
	jr z, .plan
	ld hl, PokedexInfoStatsTitle
	ld a, [wPokedexInfoPage]
	and a
	jr z, .title
	ld hl, PokedexInfoEvolutionsTitle
.title
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH + 4
.letter
	ld a, [hli]
	cp '@'
	jr z, .plan
	ld [de], a
	inc de
	jr .letter
.plan
	ld a, POKEDEX_INFO_PLAN
	ld [wPokedexInfoState], a
	ret

PokedexInfo_DrawBadge:
	ld a, [wPokedexInfoPage]
	inc a
	ld c, a
	farcall PokedexBadge_Prepare
	ret

PokedexInfo_PlanStats:
	ld a, [wPokedexInfoRow]
	and a
	jr nz, .row
	ld hl, PokedexInfoShared
	ld de, wPokedexInfoTileSources
	ld bc, POKEDEX_INFO_SHARED_TILES * 2
	call CopyBytes
	ld a, POKEDEX_INFO_SHARED_TILES
	ld [wPokedexInfoTileCount], a
.row
	ld a, [wPokedexInfoRow]
	ld e, a
	ld d, 0
	ld hl, wPokedexInfoStats
	add hl, de
	ld a, [hl]
	ld [wPokedexInfoScratch], a
	ld b, 0
.quantize
	cp 5
	jr c, .scaled
	sub 5
	inc b
	jr .quantize
.scaled
	ld a, b
	add a
	cp 102
	jr c, .width
	ld a, 101
.width
	ld [wPokedexInfoWidth], a
	ld a, [wPokedexInfoRow]
	add 10
	call PokedexInfo_RowCursor
	ld a, 1
	ld [wPokedexInfoPalette], a
	ld a, [wPokedexInfoRow]
	ld e, a
	add a
	add e
	ld e, a
	ld d, 0
	ld hl, PokedexInfoLabelTiles
	add hl, de
	ld b, 3
.label
	ld a, [hli]
	cp $ff
	jr z, .blank
	push hl
	push bc
	call PokedexInfo_ExistingTile
	pop bc
	pop hl
	jr .next_label
.blank
	push hl
	push bc
	call PokedexInfo_BlankCell
	pop bc
	pop hl
.next_label
	dec b
	jr nz, .label
	ld a, [wPokedexInfoScratch]
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, PokedexInfoNumbers
	add hl, de
	ld b, 4
.number
	ld a, [hli]
	ld e, a
	ld d, [hl]
	inc hl
	push hl
	push bc
	ld a, b
	cp 1
	jr nz, .numeric_palette
	ld a, [wPokedexInfoRow]
	add 3 ; encoded as palette + 1
	ld [wPokedexInfoPalette], a
.numeric_palette
	; Stats have a fixed 15+6*4=39-cell layout. Appending four numeric
	; glyphs is cheaper than searching the atlas for duplicates per row.
	call PokedexInfo_NewTile.new
	pop bc
	pop hl
	dec b
	jr nz, .number
	ld a, [wPokedexInfoWidth]
	sub 3
	jr c, .next
	jr z, .next
	ld b, a
.bar
	ld a, b
	cp 9
	jr c, .terminal
	sub 8
	ld b, a
	ld a, 14
	jr .part
.terminal
	dec a
	srl a
	add 10
	ld b, 0
.part
	push bc
	call PokedexInfo_ExistingTile
	pop bc
	ld a, [wPokedexInfoMapCursor]
	and 31
	cp 20
	jr z, .endpoint
	ld a, b
	and a
	jr nz, .bar
	jr .next
.endpoint
	ld a, [wPokedexInfoWidth]
	cp 100
	jr c, .next
	ld c, POKEDEX_INFO_HP_OBJ_TILE
	jr z, .endpoint_tile
	inc c
.endpoint_tile
	ld hl, wPokedexInfoOAM
	ld [hl], 96 ; screen y=80
	inc hl
	ld [hl], 163 ; screen x=155, clipped at the right border
	inc hl
	ld [hl], c
	inc hl
	ld [hl], OAM_BANK1 | 4
.next
	ld hl, wPokedexInfoRow
	inc [hl]
	ld a, [hl]
	cp 6
	ret c
	ld a, POKEDEX_INFO_COPY
	ld [wPokedexInfoState], a
	ret

PokedexInfo_RowCursor:
; a = screen tile row; cursor begins at column 1.
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wPokedexOwnerTilemapBuffer + 1
	add hl, de
	ld a, l
	ld [wPokedexInfoMapCursor], a
	ld a, h
	ld [wPokedexInfoMapCursor + 1], a
	ld de, wPokedexOwnerAttrmapBuffer - wPokedexOwnerTilemapBuffer
	add hl, de
	ld a, l
	ld [wPokedexInfoAttrCursor], a
	ld a, h
	ld [wPokedexInfoAttrCursor + 1], a
	ret

PokedexInfo_NewTile:
; de = ROM tile source. No allocator-owned species IDs survive here.
	ld hl, wPokedexInfoTileSources
	ld a, [wPokedexInfoTileCount]
	ld b, a
	ld c, 0
.find
	ld a, b
	and a
	jr z, .new
	ld a, [hli]
	cp e
	ld a, [hli]
	jr nz, .next
	cp d
	jr nz, .next
	ld a, c
	jr PokedexInfo_ExistingTile
.next
	inc c
	dec b
	jr .find
.new
	ld a, [wPokedexInfoTileCount]
	push af
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
	pop af
PokedexInfo_ExistingTile:
	ld c, a
	ld a, [wPokedexInfoAtlasBuffer]
	and a
	ld a, c
	jr z, .atlas_a
	ld e, a
	ld b, BG_BANK1
	jr .attribute
.atlas_a
	add a
	ld l, a
	ld h, 0
	ld de, PokedexInfoAtlasCells
	add hl, de
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld b, a
.attribute
	ld a, [wPokedexInfoPalette]
	dec a
	or b
	ld b, a
	ld a, e
	jr PokedexInfo_WriteCell
PokedexInfo_BlankCell:
	ld a, $32
	ld b, 0
PokedexInfo_WriteCell:
	ld hl, wPokedexInfoMapCursor
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld [de], a
	inc de
	ld [hl], d
	dec hl
	ld [hl], e
	ld hl, wPokedexInfoAttrCursor
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld a, b
	ld [de], a
	inc de
	ld [hl], d
	dec hl
	ld [hl], e
	ret

PokedexInfo_PlanEvolution:
; One mini-sprite or text line per slice; the third-line job is skipped.
	ld a, [wPokedexInfoRow]
	and 3
	jp nz, .text
	ld a, [wPokedexInfoRow]
	srl a
	srl a
	ld b, a
	ld a, [wPokedexInfoPage]
	dec a
	add a
	add b
	ld b, a
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
	ld de, PokedexInfoSpecies
	add hl, de
	ld a, b
	cp [hl]
	jp nc, .copy
	ld a, [wPokedexInfoEvolutionList]
	ld l, a
	ld a, [wPokedexInfoEvolutionList + 1]
	ld h, a
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, l
	ld [wPokedexInfoEvolutionList], a
	ld a, h
	ld [wPokedexInfoEvolutionList + 1], a
	ld h, d
	ld l, e
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, l
	ld [wPokedexInfoEvolutionRecord], a
	ld a, h
	ld [wPokedexInfoEvolutionRecord + 1], a
	ld h, d
	ld l, e
	call GetPokemonIDFromIndex
	ld c, a
	farcall ReadMonMenuIconForPokedex
	ld a, c
	swap a
	and $f
	push af
	ld a, [wPokedexInfoMiniCount]
	and a
	ld hl, wPokedexInfoMiniGFX
	jr z, .mini_destination
	ld hl, wPokedexInfoMiniGFX + 8 tiles
.mini_destination
	push hl
	ld h, d
	ld l, e
	pop de
	ld a, b
	ld bc, 8 tiles
	call FarCopyBytes
	pop af
	call PokedexInfo_PrepareMiniPalette
	call PokedexInfo_PrepareMiniOAM
	ld a, POKEDEX_INFO_MINI_UPLOAD
	ld [wPokedexInfoState], a
	ret
.text
	ld a, [wPokedexInfoLineRemaining]
	and a
	jr nz, .continue_text
	ld a, [wPokedexInfoEvolutionRecord]
	ld l, a
	ld a, [wPokedexInfoEvolutionRecord + 1]
	ld h, a
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, l
	ld [wPokedexInfoEvolutionRecord], a
	ld a, h
	ld [wPokedexInfoEvolutionRecord + 1], a
	ld a, [wPokedexInfoRow]
	ld b, a
	and 3
	dec a
	ld c, a
	ld a, b
	and 4
	jr z, .first_entry
	ld a, 3
.first_entry
	add c
	add 11
	push de
	call PokedexInfo_RowCursor
	call PokedexInfo_BlankCell
	call PokedexInfo_BlankCell
	call PokedexInfo_BlankCell
	ld a, 1
	ld [wPokedexInfoPalette], a
	pop hl
	ld b, [hl]
	inc hl
	ld a, l
	ld [wPokedexInfoLineSource], a
	ld a, h
	ld [wPokedexInfoLineSource + 1], a
	ld a, b
	ld [wPokedexInfoLineRemaining], a
.continue_text
	ld a, [wPokedexInfoLineSource]
	ld l, a
	ld a, [wPokedexInfoLineSource + 1]
	ld h, a
	ld b, 4
.glyph
	ld a, [wPokedexInfoLineRemaining]
	and a
	jr z, .next
	ld a, [hli]
	ld e, a
	ld d, [hl]
	inc hl
	push hl
	push bc
	call PokedexInfo_NewTile
	pop bc
	pop hl
	ld a, l
	ld [wPokedexInfoLineSource], a
	ld a, h
	ld [wPokedexInfoLineSource + 1], a
	push hl
	ld hl, wPokedexInfoLineRemaining
	dec [hl]
	pop hl
	jr z, .next
	dec b
	jr nz, .glyph
	ret
.next
	ld hl, wPokedexInfoRow
	inc [hl]
	ld a, [hl]
	and 3
	cp 3
	jr nz, .check_end
	inc [hl]
.check_end
	ld a, [hl]
	cp 8
	ret c
.copy
	ld a, POKEDEX_INFO_COPY
	ld [wPokedexInfoState], a
	ret

PokedexInfo_UploadMini:
; Keep species lookup/copy and hardware upload in separate admitted slices.
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexInfoMiniGFX
	ld de, vTiles3 tile POKEDEX_INFO_MINI_OBJ_TILE
	ld a, [wPokedexInfoMiniBuffer]
	and a
	jr z, .buffer
	ld de, vTiles3 tile (POKEDEX_INFO_MINI_OBJ_TILE + 16)
.buffer
	ld a, [wPokedexInfoMiniCount]
	and a
	jr z, .upload
	ld hl, wPokedexInfoMiniGFX + 8 tiles
	ld a, e
	add LOW(8 tiles)
	ld e, a
	jr nc, .upload
	inc d
.upload
	ld c, 8
	call PokedexInfo_UploadSafeGFX
	pop af
	ldh [rVBK], a
	ld hl, wPokedexInfoMiniCount
	inc [hl]
	ld a, POKEDEX_INFO_PLAN
	ld [wPokedexInfoState], a
	jp PokedexInfo_PlanEvolution.next

PokedexInfo_PrepareMiniPalette:
	add a
	add a
	add a
	ld l, a
	ld h, 0
	ld de, PartyMenuOBPals
	add hl, de
	ld de, wPokedexInfoMiniPalettes
	ld a, [wPokedexInfoMiniCount]
	and a
	jr z, .copy
	ld de, wPokedexInfoMiniPalettes + 1 palettes
.copy
	ld a, BANK(PartyMenuOBPals)
	ld bc, 1 palettes
	jp FarCopyBytes

PokedexInfo_PrepareMiniOAM:
	ld hl, wPokedexInfoOAM
	ld a, [wPokedexInfoMiniCount]
	ld b, 104
	ld c, POKEDEX_INFO_MINI_OBJ_TILE
	ld d, OAM_BANK1 | 2
	and a
	jr z, .buffer
	ld hl, wPokedexInfoOAM + 16
	ld b, 128
	ld c, POKEDEX_INFO_MINI_OBJ_TILE + 8
	inc d
.buffer
	ld a, [wPokedexInfoMiniBuffer]
	and a
	jr z, .sprites
	ld a, c
	add 16
	ld c, a
.sprites
	ld a, b
	ld [hli], a
	ld a, 16
	ld [hli], a
	ld a, c
	ld [hli], a
	ld a, d
	ld [hli], a
	inc c
	ld a, b
	ld [hli], a
	ld a, 24
	ld [hli], a
	ld a, c
	ld [hli], a
	ld a, d
	ld [hli], a
	inc c
	ld a, b
	add 8
	ld [hli], a
	ld a, 16
	ld [hli], a
	ld a, c
	ld [hli], a
	ld a, d
	ld [hli], a
	inc c
	ld a, b
	add 8
	ld [hli], a
	ld a, 24
	ld [hli], a
	ld a, c
	ld [hli], a
	ld [hl], d
	ret

PokedexInfo_CopyTiles:
	ld b, 8
.tile
	ld a, [wPokedexInfoCopyTile]
	ld c, a
	ld a, [wPokedexInfoTileCount]
	cp c
	jr z, .ready
	push bc
	ld a, c
	add a
	ld l, a
	ld h, 0
	ld de, wPokedexInfoTileSources
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	push hl
	ld h, 0
	ld l, c
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wPokedexInfoGFX
	add hl, de
	ld d, h
	ld e, l
	pop hl
	ld bc, TILE_SIZE
	ld a, BANK(PokedexInfoTileGFX)
	call FarCopyBytes
	ld hl, wPokedexInfoCopyTile
	inc [hl]
	pop bc
	dec b
	jr nz, .tile
	ret
.ready
	ld a, POKEDEX_INFO_UPLOAD
	ld [wPokedexInfoState], a
	ret

PokedexInfo_UploadTiles:
; At most eight already-copied glyphs into the inactive atlas. Never overwrite
; visible text or combine this DMA with the final map publication.
	ld a, [wPokedexInfoUploadTile]
	ld c, a
	ld a, [wPokedexInfoTileCount]
	sub c
	jp z, .ready
	ld b, a
	ld a, [wPokedexInfoAtlasBuffer]
	and a
	jr z, .atlas_a
	ld a, TRUE
	ld [wPokedexInfoListingCacheDirty], a
	ld a, c
	ld de, vTiles5
	jr .destination
.atlas_a
	ld a, c
	cp 6
	ld d, 6
	jr c, .run
	cp 16
	ld d, 16
	jr c, .run
	cp 24
	ld d, 24
	jr c, .run
	cp 32
	ld d, 32
	jr c, .run
	ld d, 40
.run
	ld a, d
	sub c
	cp b
	jr nc, .count
	ld b, a
.count
	ld a, c
	add a
	ld l, a
	ld h, 0
	ld de, PokedexInfoAtlasCells
	add hl, de
	ld a, [hl]
	xor $80
	ld de, vTiles4
.destination
	push bc
	ld c, a
	and $f0
	swap a
	add d
	ld d, a
	ld a, c
	and $f
	swap a
	add e
	ld e, a
	pop bc
	ld a, b
	cp 9
	jr c, .bounded
	ld a, 8
.bounded
	push af
	push de
	ld a, c
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wPokedexInfoGFX
	add hl, de
	pop de
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld a, b
	cp 9
	jr c, .transfer
	ld a, 8
.transfer
	ld c, a
	call PokedexInfo_UploadSafeGFX
	pop af
	ldh [rVBK], a
	pop bc
	ld a, [wPokedexInfoUploadTile]
	add b
	ld [wPokedexInfoUploadTile], a
	ret
.ready
	jp PokedexInfo_BeginRecord

PokedexInfo_UploadSafeGFX:
; The cry IRQ changes SVBK. HDMA must therefore read unbanked WRAM, not the
; Info workspace. The mainline animation upload has returned before this
; helper runs and reconstructs its payload before its next upload.
	push bc
	push de
	ld de, POKEDEX_ANIM_PAYLOAD
	ld a, c
	swap a
	ld c, a
	ld b, 0
	call CopyBytes
	pop de
	pop bc
	ld hl, POKEDEX_ANIM_PAYLOAD
	jp Pokedex_HDMATransferCacheGFX

INCLUDE "engine/pokedex/pokedex_info_return.asm"

PokedexInfo_RestoreListingCache:
; Atlas B borrows only the Listing's BG frame-0 icons. Invalidate the ring
; before its normal hidden rebuild; no stale cache tags may survive.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoListingCacheDirty)
	ldh [rSVBK], a
	ld a, [wPokedexInfoListingCacheDirty]
	and a
	jr z, .done
	xor a
	ld [wPokedexInfoListingCacheDirty], a
	ld a, $ff
	ld hl, wPokedexGridCacheRowOffsets
	ld bc, POKEDEX_GRID_CACHE_ROWS * 2
	call ByteFill
.done
	pop af
	ldh [rSVBK], a
	ret

PokedexInfo_StagePalettes:
; WRAM palette targets only. The publisher owns the hardware writes.
	ld a, [wPokedexInfoPage]
	and a
	ret z
.mini_palettes
	ld hl, wPokedexInfoMiniPalettes
	ld de, wOBPals2 palette 2
	ld b, 2 palettes
.byte
	ld a, [hli]
	push af
	ld a, BANK(wOBPals2)
	ldh [rSVBK], a
	pop af
	ld [de], a
	inc de
	ld a, BANK(wPokedexInfoMiniPalettes)
	ldh [rSVBK], a
	dec b
	jr nz, .byte
	ret

PokedexInfo_StageStaticPalettes:
; Colors 0/3 keep the footprint identical on Description and Info.
	ld hl, PokedexInfoStatPalettes
	ld de, wBGPals2 palette 2
	ld bc, 6 palettes
	ld a, BANK(wBGPals2)
	call FarCopyWRAM
	ld de, wOBPals2 palette 4
	ld bc, 1 palettes
	ld a, BANK(wOBPals2)
; The endpoint uses the same border/fill but OBJ color 0 is transparent.
	ld hl, PokedexInfoStatPalettes
	call FarCopyWRAM
	ret

PokedexInfo_StageOAM:
	ld a, TRUE
	ldh [hOAMUpdate], a
	ld hl, wPokedexInfoOAM
	ld de, wShadowOAMSprite08
	ld bc, 8 * 4
	call CopyBytes
	ret

PokedexInfo_LoadTypeSprites:
	ldh a, [hCGB]
	and a
	ret z
	ld a, [wPokedexSelectedSpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBaseType1]
	ld de, wPokedexWRAM0Scratch
	call .CopyType
	ld a, [wBaseType1]
	ld b, a
	ld a, [wBaseType2]
	cp b
	ld c, 4
	jr z, .upload
	ld de, wPokedexWRAM0Scratch + 4 tiles
	call .CopyType
	ld c, 8
.upload
	push bc
	ldh a, [rVBK]
	push af
	ld a, 1
	ldh [rVBK], a
	ld hl, wPokedexWRAM0Scratch
	ld de, vTiles3 tile POKEDEX_TYPE_OBJ_TILE
	ld a, [POKEDEX_DESCRIPTION_ICON_BUFFER]
	and a
	jr z, .destination
	ld de, vTiles3 tile (POKEDEX_TYPE_OBJ_TILE + 8)
.destination
	call Pokedex_HDMATransferCacheGFX
	pop af
	ldh [rVBK], a
	pop bc
	ld a, [POKEDEX_DESCRIPTION_ICON_BUFFER]
	and a
	ld a, POKEDEX_TYPE_OBJ_TILE
	jr z, .oam
	add 8
.oam
	ld b, a
	ld hl, wShadowOAMSprite00
	ld d, 75 ; x=67
	ld e, OAM_BANK1
.sprite
	ld a, 72 ; y=56
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
	ld d, 115 ; second badge x=107
	inc e
.next
	dec c
	jr nz, .sprite
	ret
.CopyType:
	push de
	ld e, a
	ld d, 0
	ld hl, CompactTypeIconGFXPointers
	add hl, de
	add hl, de
	add hl, de
	ld a, BANK(CompactTypeIconGFXPointers)
	call GetFarByte
	push af
	inc hl
	ld a, BANK(CompactTypeIconGFXPointers)
	call GetFarWord
	pop af
	pop de
	push de
	ld bc, 4 tiles
	call FarCopyBytes
	pop hl
	set 7, [hl]
	ld de, 14
	add hl, de
	set 7, [hl]
	ld de, 34
	add hl, de
	set 0, [hl]
	ld de, 14
	add hl, de
	set 0, [hl]
	ld de, -62
	add hl, de
	ld b, 32
.remap
	ld a, [hli]
	xor [hl]
	cpl ; BG background 1 -> OBJ transparency 0; white 0 -> white 1
	dec hl
	ld [hli], a
	inc hl
	dec b
	jr nz, .remap
	ret

PokedexInfo_StageTypePalettes:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wBaseType1)
	ldh [rSVBK], a
	ld a, [wPokedexSelectedSpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBaseType1]
	ld de, wOBPals2
	call .type
	ld a, [wBaseType2]
	ld de, wOBPals2 palette 1
	call .type
	ld hl, wOBPals2
	ld de, wOBPals1
	ld bc, 2 palettes
	ld a, BANK(wOBPals2)
	call FarCopyWRAM
	ld a, %00000011
	ld [wPokedexSelectedOBJPaletteDirty], a
	pop af
	ldh [rSVBK], a
	ret
.type
	push de
	ld e, a
	ld d, 0
	ld hl, TypeIconPalettePointers
	add hl, de
	add hl, de
	ld a, BANK(TypeIconPalettePointers)
	call GetFarWord
	pop de
	ldh a, [rSVBK]
	push af
	ld a, BANK(wOBPals2)
	ldh [rSVBK], a
	push de
	ld a, BANK(TypeIconPalettes)
	ld bc, 1 palettes
	call FarCopyBytes
	pop hl
	ld a, [hli]
	ld b, [hl]
	inc hl
	ld [hli], a
	ld [hl], b
	pop af
	ldh [rSVBK], a
	ret

PokedexInfoStatPalettes:
; white, border, fill, panel background. HP also owns the 1bpp footprint.
	RGB 31,31,31, 11,22,2, 13,27,2, 5,5,5
	RGB 31,31,31, 25,22,3, 29,25,3, 5,5,5
	RGB 31,31,31, 23,10,2, 28,12,2, 5,5,5
	RGB 31,31,31, 2,19,24, 2,24,29, 5,5,5
	RGB 31,31,31, 8,11,22, 9,13,27, 5,5,5
	RGB 31,31,31, 20,3,16, 26,4,21, 5,5,5

PokedexInfoAtlasCells:
FOR cell_id, $fa, $100
	db cell_id, BG_BANK1
ENDR
FOR cell_id, $28, $32
	db cell_id, BG_BANK1
ENDR
FOR cell_id, $78, $80
	db cell_id, BG_BANK1
ENDR
FOR cell_id, $64, $6c
	db cell_id, BG_BANK1
ENDR
FOR cell_id, $70, $78
	db cell_id, BG_BANK1
ENDR
.end
ASSERT .end - PokedexInfoAtlasCells == POKEDEX_INFO_TILES * 2
