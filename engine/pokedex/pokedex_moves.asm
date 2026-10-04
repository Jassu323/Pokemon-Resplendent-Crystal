; Bounded native-font Moves renderer; portrait owns priority.

PokedexMoves_Activate:
	ldh a, [hCGB]
	and a
	ret z
	farcall PokedexInfo_Cancel
	ldh a, [rSVBK]
	push af
	ld a, 3
	ldh [rSVBK], a
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_MOVES
	jr nz, .first
	ld a, [wPokedexMovesPage]
	inc a
	ld hl, wPokedexMovesPageCount
	cp [hl]
	jr c, .page
.first
	xor a
.page
	ld [wPokedexMovesPage], a
	ld a, DEXSELECT_VIEW_MOVES
	ld [wPokedexSelectedView], a
	ld a, 1
	ld [wPokedexMovesState], a
	pop af
	ldh [rSVBK], a
	ret

PokedexMoves_PrepareInitial:
	ldh a, [rSVBK]
	push af
	ld a, 3
	ldh [rSVBK], a
	xor a
	ld [wPokedexMovesPage], a
	ld a, 1
	ld [wPokedexMovesState], a
.step
	call PokedexMoves_Step
	ld a, [wPokedexMovesState]
	cp 4
	jr nz, .step
	call PokedexMoves_StageOAM
	pop af
	ldh [rSVBK], a
	ret

PokedexMoves_Service:
	ldh a, [hCGB]
	and a
	ret z
	ldh a, [rSVBK]
	push af
	ld a, 3
	ldh [rSVBK], a
	ld a, [wPokedexOwnerTransition]
	and a
	jr nz, .request
	ld b, 3
.slice
	ld a, [wPokedexMovesState]
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
	cp 64
	jr nc, .done
.admit
	ld a, [wPokedexMovesState]
	cp 4
	jr z, .publish
	push bc
	call PokedexMoves_Step
	pop bc
	dec b
	jr nz, .slice
	jr .done
.publish
	di
	call PokedexMoves_StageOAM
	ld a, POKEDEX_OWNER_TRANSITION_INFO
	ld [wPokedexOwnerTransition], a
	ei
.request
	ldh a, [hVBlank]
	or VBLANK_POKEDEX
	ldh [hVBlank], a
.done
	pop af
	ldh [rSVBK], a
	ret

PokedexMoves_StageOAM:
	xor a
	ld hl, wShadowOAMSprite08
	ld bc, 8 * 4
	call ByteFill
	ld a, TRUE
	ldh [hOAMUpdate], a
	ret

PokedexMoves_Step:
	ld a, [wPokedexMovesState]
	cp 1
	jp z, PokedexMoves_Initialize
	cp 2
	jp z, PokedexMoves_ClearRow
	cp 3
	jp z, PokedexMoves_DrawRow
	ret

PokedexMoves_Initialize:
	xor a
	ld [wPokedexMovesRow], a
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, de ; 17-byte record
	ld de, PokedexMovesSpecies
	add hl, de
	ld a, BANK(PokedexMovesSpecies)
	call GetFarByte
	ld [wPokedexMovesPageCount], a
	inc hl
	ld a, [wPokedexMovesPage]
	ld [wPokedexMovesScratch], a
	xor a
	ld [wPokedexMovesCategory], a
	ld a, [wPokedexInfoCaught]
	and a
	jr nz, .category
	ld a, 1
	ld [wPokedexMovesPageCount], a
	xor a
	ld [wPokedexMovesPage], a
	ld [wPokedexMovesRemaining], a
	jr .ready
.category
	ld a, BANK(PokedexMovesSpecies)
	call GetFarByte
	ld [wPokedexMovesRemaining], a
	ld b, 0
.pages
	and a
	jr z, .pages_done
	inc b
	sub 5
	jr nc, .pages
.pages_done
	ld a, [wPokedexMovesScratch]
	cp b
	jr c, .found
	sub b
	ld [wPokedexMovesScratch], a
	ld de, 4
	add hl, de
	ld a, [wPokedexMovesCategory]
	inc a
	ld [wPokedexMovesCategory], a
	cp 4
	jr c, .category
	xor a
	ld [wPokedexMovesRemaining], a
	jr .ready
.found
	ld c, a
	add a
	add a
	add c ; 5 * local page, <= 255
	ld c, a
	ld a, [wPokedexMovesRemaining]
	sub c
	cp 6
	jr c, .count
	ld a, 5
.count
	ld [wPokedexMovesRemaining], a
	inc hl
	ld a, BANK(PokedexMovesSpecies)
	call GetFarByte
	ld [wPokedexMovesSourceBank], a
	inc hl
	ld a, BANK(PokedexMovesSpecies)
	call GetFarWord
	ld a, [wPokedexMovesCategory]
	and a
	ld b, 0
	jr nz, .egg
	add hl, bc
	add hl, bc
	jr .offset
.egg
	cp 3
	jr nz, .offset
	add hl, bc
.offset
	add hl, bc
	ld a, l
	ld [wPokedexMovesSource], a
	ld a, h
	ld [wPokedexMovesSource + 1], a
.ready
	ld a, 2
	ld [wPokedexMovesState], a
	ret

PokedexMoves_ClearRow:
	ld a, [wPokedexMovesRow]
	add 9
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wPokedexOwnerTilemapBuffer
	add hl, de
	push hl
	ld a, $32
	ld bc, TILEMAP_WIDTH
	call ByteFill
	pop hl
	ld [hl], $36
	push hl
	ld de, SCREEN_WIDTH
	add hl, de
	ld [hl], $67
	pop hl
	ld de, wPokedexOwnerAttrmapBuffer - wPokedexOwnerTilemapBuffer
	add hl, de
	xor a
	ld bc, TILEMAP_WIDTH
	call ByteFill
	ld hl, wPokedexMovesRow
	inc [hl]
	ld a, [hl]
	cp 7
	ret c
	xor a
	ld [hl], a
	ld a, [wPokedexMovesPage]
	inc a
	ld c, a
	call PokedexBadge_Prepare
	ld a, [wPokedexInfoCaught]
	and a
	jr z, .empty
	ld a, [wPokedexMovesCategory]
	add a
	ld e, a
	ld d, 0
	ld hl, .Titles
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH + 7
	call PokedexMoves_CopyText
	ld a, 3
	ld [wPokedexMovesState], a
	ret
.empty
	ld a, 4
	ld [wPokedexMovesState], a
	ret
.Titles
	dw .Level, .Machine, .Tutor, .Egg
.Level db "Level Up@"
.Machine db "TM/HM@"
.Tutor db "Move Tutor@"
.Egg db "Breeding@"

PokedexMoves_DrawRow:
	ld a, [wPokedexMovesRemaining]
	and a
	jp z, .ready
	ld a, [wPokedexMovesSource]
	ld l, a
	ld a, [wPokedexMovesSource + 1]
	ld h, a
	ld a, [wPokedexMovesSourceBank]
	call GetFarByte
	ld c, a
	ld a, [wPokedexMovesCategory]
	and a
	jr z, .level
	cp 3
	jr z, .egg
	inc hl
	push hl
	ld a, c
	dec a
	ld c, a
	ld a, [wPokedexMovesCategory]
	cp 2
	jr nz, .machine
	ld a, c
	add 57
	ld c, a
.machine
	ld b, 0
	ld hl, PokedexMovesMachineMoves
	add hl, bc
	add hl, bc
	ld a, BANK(PokedexMovesMachineMoves)
	call GetFarWord
	ld d, h
	ld e, l
	pop hl
	jr .move
.level
	inc hl
.egg
	push hl
	ld a, [wPokedexMovesSourceBank]
	call GetFarWord
	ld d, h
	ld e, l
	pop hl
	inc hl
	inc hl
.move
	ld a, l
	ld [wPokedexMovesSource], a
	ld a, h
	ld [wPokedexMovesSource + 1], a
	push de ; stable 16-bit move index
	ld a, [wPokedexMovesRow]
	add 11
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, wPokedexOwnerTilemapBuffer + 2
	add hl, de
	push hl
	ld a, [wPokedexMovesCategory]
	and a
	jr z, .level_prefix
	cp 3
	jr z, .egg_prefix
	cp 2
	jr z, .tutor_prefix
	ld a, "T"
	ld [hli], a
	ld a, "M"
	ld [hli], a
	ld a, c
	inc a
	cp 51
	jr c, .number
	sub 50
	ld c, a
	dec hl
	dec hl
	ld [hl], "H"
	inc hl
	inc hl
	ld a, c
	jr .number
.level_prefix
	ld [hl], $7d ; dedicated battle-level glyph
	inc hl
	ld a, c
.number
	call PokedexMoves_Number
	jr .name
.egg_prefix
	ld de, .EggPrefix
	jr .prefix
.tutor_prefix
	ld de, .TutorPrefix
.prefix
.letter
	ld a, [de]
	cp "@"
	jr z, .name
	inc de
	ld [hli], a
	jr .letter
.name
	pop hl
	ld de, 5
	add hl, de
	pop de
	push hl
	ld h, d
	ld l, e
	dec hl
	add hl, hl
	ld de, PokedexMovesNamePointers
	add hl, de
	ld a, BANK(PokedexMovesNamePointers)
	call GetFarWord
	ld d, h
	ld e, l
	pop hl
	ld a, BANK(MoveNames)
.name_letter
	push af
	push hl
	ld h, d
	ld l, e
	call GetFarByte
	pop hl
	cp "@"
	jr z, .name_done
	ld [hli], a
	inc de
	pop af
	jr .name_letter
.name_done
	pop af
	ld hl, wPokedexMovesRow
	inc [hl]
	ld hl, wPokedexMovesRemaining
	dec [hl]
	ret
.ready
	ld a, 4
	ld [wPokedexMovesState], a
	ret
.EggPrefix db "Egg@"
.TutorPrefix db "Tut@"

PokedexMoves_Number:
; Two digits, or three if a future level is >= 100.
	ld b, "0" - 1
.hundreds
	inc b
	sub 100
	jr nc, .hundreds
	add 100
	ld c, a
	ld a, b
	cp "0"
	jr z, .tens_start
	ld [hli], a
.tens_start
	ld a, c
	ld b, "0" - 1
.tens
	inc b
	sub 10
	jr nc, .tens
	add 10
	add "0"
	ld c, a
	ld a, b
	ld [hli], a
	ld [hl], c
	ret

PokedexMoves_CopyText:
	ld a, [hli]
	cp "@"
	ret z
	ld [de], a
	inc de
	jr PokedexMoves_CopyText

PokedexBadge_Prepare:
; Bank 3 selected; c=1..19 survives FarCall. Upload the unpublished buffer.
	ld a, c
	ld [wPokedexBadgePage], a
	ld a, [wPokedexBadgeActive]
	xor 1
	ld [wPokedexBadgePending], a
	ld a, c
	cp 10
	jr nc, .double
	add a
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, PokedexBadgeSingleGFX
	jr .source
.double
	sub 8
	cp 2
	jr nz, .column
	dec a
.column
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, PokedexBadgeDoubleGFX
.source
	add hl, de
	ld de, wPokedexBadgeGFX
	ld bc, 2 tiles
	call CopyBytes
	ldh a, [rVBK]
	push af
	xor a
	ldh [rVBK], a
	ld hl, wPokedexBadgeGFX
	ld de, vTiles2 tile $73
	ld a, [wPokedexBadgePending]
	and a
	jr z, .upper
	ld de, vTiles2 tile $79
.upper
	ld b, 16
	call .copy
	ld de, vTiles2 tile $78
	ld a, [wPokedexBadgePending]
	and a
	jr z, .lower
	ld de, vTiles2 tile $7a
.lower
	ld b, 16
	call .copy
	pop af
	ldh [rVBK], a
	ld b, $73
	ld c, $78
	ld a, [wPokedexBadgePending]
	and a
	jr z, .map
	ld b, $79
	ld c, $7a
.map
	ld a, b
	ld [wPokedexOwnerTilemapBuffer + 8 * TILEMAP_WIDTH + 2], a
	ld a, c
	ld [wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH + 2], a
	ld a, $77
	ld [wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH + 1], a
	ld b, $74
	ld c, $32
	ld a, [wPokedexBadgePage]
	cp 10
	jr c, .end
	ld b, $7b
	ld c, $7c
.end
	ld a, b
	ld [wPokedexOwnerTilemapBuffer + 8 * TILEMAP_WIDTH + 3], a
	ld a, c
	ld [wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH + 3], a
	ret
.copy
.wait
	di
	ldh a, [rSTAT]
	and STAT_BUSY
	jr nz, .busy
	ld a, [hli]
	ld [de], a
	ei
	inc de
	dec b
	jr nz, .copy
	ret
.busy
	ei
	jr .wait

PokedexBadgeSingleGFX:
	INCBIN "gfx/pokedex/pokedex_page_numbers.2bpp"
PokedexBadgeDoubleGFX:
	INCBIN "gfx/pokedex/pokedex_page_numbers_double_digits.2bpp"
PokedexBadgePermanentGFX:
	INCBIN "gfx/pokedex/pokedex_page_numbers_double_digits.2bpp", 4 tiles, 2 tiles
	INCBIN "build/dex-moves-assets/level.2bpp"
