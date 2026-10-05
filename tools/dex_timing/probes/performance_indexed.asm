; PRIVATE PERFORMANCE PROTOTYPE. All pointers and maps are generated from data.
PokedexPerf_FastStatsRow:
	ld a, [wPokedexInfoRow]
	and a
	jr nz, .row
	ld hl, PokedexInfoShared
	ld de, wPokedexInfoTileSources
	ld bc, 30
	ld a, BANK(PokedexInfoShared)
	call FarCopyBytes
	ld a, 39
	ld [wPokedexInfoTileCount], a
	ld a, [wPokedexInfoStats]
	cp 250
	jr c, .row
	ld c, POKEDEX_INFO_HP_OBJ_TILE
	cp 255
	jr c, .endpoint
	inc c
.endpoint
	ld hl, wPokedexInfoOAM
	ld [hl], 96
	inc hl
	ld [hl], 163
	inc hl
	ld [hl], c
	inc hl
	ld [hl], OAM_BANK1 | 4
.row
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
	ld de, PokedexPerf_StatsIndex
	add hl, de
	ld a, [hli]
	push af
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [wPokedexInfoRow]
	ld de, 46
.offset
	and a
	jr z, .source
	add hl, de
	dec a
	jr .offset
.source
	pop af
	ld de, wPokedexInfoMiniGFX
	ld bc, 46
	call FarCopyBytes
	ld a, [wPokedexInfoRow]
	add 10
	ld l, a
	ld h, 0
REPT 5
	add hl, hl
ENDR
	ld de, wPokedexOwnerTilemapBuffer + 1
	add hl, de
	ld d, h
	ld e, l
	push de
	ld hl, wPokedexInfoMiniGFX
	ld b, 19
.map
	ld a, [hli]
	cp $ff
	jr z, .blank
	ld c, a
	ld a, [wPokedexInfoAtlasBuffer]
	and a
	ld a, c
	jr nz, .write
	push hl
	push de
	ld hl, PokedexPerf_AtlasCells
	ld e, a
	ld d, 0
	add hl, de
	ld a, [hl]
	pop de
	pop hl
	jr .write
.blank
	ld a, $32
.write
	ld [de], a
	inc de
	dec b
	jr nz, .map
	pop hl
	ld de, wPokedexOwnerAttrmapBuffer - wPokedexOwnerTilemapBuffer
	add hl, de
	ld d, h
	ld e, l
	ld hl, wPokedexInfoMiniGFX + 19
	ld bc, 19
	call CopyBytes
	ld a, [wPokedexInfoRow]
	add a
	add a
	add a
	add 30
	ld l, a
	ld h, 0
	ld de, wPokedexInfoTileSources
	add hl, de
	ld d, h
	ld e, l
	ld hl, wPokedexInfoMiniGFX + 38
	ld bc, 8
	call CopyBytes
	ld hl, wPokedexInfoRow
	inc [hl]
	ld a, [hl]
	cp 6
	ret c
	ld a, POKEDEX_INFO_COPY
	ld [wPokedexInfoState], a
	ret

PokedexPerf_AtlasCells:
FOR id, $fa, $100
	db id
ENDR
FOR id, $28, $32
	db id
ENDR
FOR id, $78, $80
	db id
ENDR
FOR id, $64, $6c
	db id
ENDR
FOR id, $70, $78
	db id
ENDR

PokedexPerf_FastNests:
	push de
	hlcoord 0, 0
	ld bc, SCREEN_AREA
	xor a
	call ByteFill
	ld a, [wNamedObjectIndex]
	call GetPokemonIndexFromID
	dec hl
	add hl, hl
	add hl, hl
	pop de
	ld a, e
	and a
	jr z, .johto
	inc hl
	inc hl
.johto
	push af
	ld de, PokedexPerf_NestIndex
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [hli]
	ld c, a
	ld b, 0
	decoord 0, 0
	and a
	call nz, CopyBytes
	pop af
	and a
	ret nz
	farcall FindNest.RoamMon1
	farcall FindNest.RoamMon2
	ret

INCLUDE "build/dex-performance-assets/indexed-tables.asm"
