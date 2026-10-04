ASSERT wPokedexDescriptionTextChunkEnd - wPokedexDescriptionTextChunk == POKEDEX_DESCRIPTION_TEXT_CHUNK

PokedexSelectedMon_CancelDescriptionText:
	ldh a, [hCGB]
	and a
	ret z
	ld a, [wPokedexOwnerTransition]
	cp POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT
	jr nz, .clear_job
	xor a
	ld [wPokedexOwnerTransition], a
.clear_job
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexDescriptionTextState)
	ldh [rSVBK], a
	xor a
	ld [wPokedexDescriptionTextState], a
	pop af
	ldh [rSVBK], a
	ret

PokedexSelectedMon_ServiceDescriptionText:
; Animation has first use of this interval. A bounded text slice is admitted
; only with time left for interrupts, audio refill and the owner-loop return.
	ldh a, [hCGB]
	and a
	ret z
	ld a, [wPokedexOwnerTransition]
	cp POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT
	jr nz, .not_ready
	; A competing portrait publication may clear the one-shot IRQ request.
	ldh a, [hVBlank]
	or VBLANK_POKEDEX
	ldh [hVBlank], a
	ret
.not_ready
	and a
	ret nz
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexDescriptionTextState)
	ldh [rSVBK], a
	ld c, POKEDEX_DESCRIPTION_TEXT_SLICES
.slice
	ld a, [wPokedexOwnerTransition]
	and a
	jr nz, .done
	ldh a, [rLY]
	cp LY_VBLANK
	jr nc, .admitted
	cp POKEDEX_DESCRIPTION_TEXT_LATEST_LY
	jr c, .admitted
	ld a, [wPokedexAnimPlaybackState]
	cp POKEDEX_ANIM_PLAYBACK_PLAYING
	jr z, .done
.admitted
	ld a, [wPokedexDescriptionTextState]
	and a
	jr z, .done
	cp POKEDEX_DESCRIPTION_TEXT_BADGE
	jr nz, .not_badge
	push bc
	call PokedexSelectedMon_PrepareDescriptionBadge
	pop bc
	jr .next_slice
.not_badge
	cp POKEDEX_DESCRIPTION_TEXT_INITIALIZE
	jr nz, .chunk
	push bc
	call PokedexSelectedMon_InitializeDescriptionText
	pop bc
	jr .next_slice
.chunk
	push bc
	call PokedexSelectedMon_RenderDescriptionTextChunk
	pop bc
.next_slice
	dec c
	jr nz, .slice
.done
	pop af
	ldh [rSVBK], a
	ret

PokedexSelectedMon_InitializeDescriptionText:
	ld a, [wPokedexDescriptionPage]
	ld [wPokedexDescriptionTextPage], a
	ld a, [wPokedexSelectedSpecies]
	ld b, a
	farcall GetDexEntryPointer
	ld a, b
	ld [wPokedexDescriptionTextBank], a
	ld a, e
	ld [wPokedexDescriptionTextSource], a
	ld a, d
	ld [wPokedexDescriptionTextSource + 1], a
	ld a, POKEDEX_DESCRIPTION_TEXT_BADGE
	ld [wPokedexDescriptionTextState], a
	xor a
	ld [wPokedexDescriptionTextRow], a
	hlcoord 2, 10
	ld de, wPokedexOwnerTilemapBuffer + 10 * TILEMAP_WIDTH + 2
	ld a, ' '
REPT 5
	REPT SCREEN_WIDTH - 2
		ld [hli], a
		ld [de], a
		inc de
	ENDR
	inc hl
	inc hl
	push hl
	ld hl, TILEMAP_WIDTH - (SCREEN_WIDTH - 2)
	add hl, de
	ld d, h
	ld e, l
	pop hl
ENDR
	hlcoord 2, 10
	ld de, wPokedexOwnerTilemapBuffer + 10 * TILEMAP_WIDTH + 2
	jp PokedexSelectedMon_SaveDescriptionTextCursor

PokedexSelectedMon_PrepareDescriptionBadge:
	ld a, [wPokedexDescriptionTextPage]
	inc a
	ld c, a
	farcall PokedexBadge_Prepare
	ld a, POKEDEX_DESCRIPTION_TEXT_CATEGORY
	ld [wPokedexDescriptionTextState], a
	ret

PokedexSelectedMon_RenderDescriptionTextChunk:
	ld hl, wPokedexDescriptionTextSource
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld de, wPokedexDescriptionTextChunk
	ld bc, POKEDEX_DESCRIPTION_TEXT_CHUNK
	ld a, [wPokedexDescriptionTextBank]
	call FarCopyBytes
	ld hl, wPokedexDescriptionTextCursor
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [wPokedexDescriptionTextOwnerCursor]
	ld e, a
	ld a, [wPokedexDescriptionTextOwnerCursor + 1]
	ld d, a
	ld bc, wPokedexDescriptionTextChunk
.next
	ld a, [wPokedexDescriptionTextState]
	cp POKEDEX_DESCRIPTION_TEXT_RENDER
	jr z, .render
	ld a, [bc]
	inc bc
	cp '@'
	jr nz, .check_end
	ld a, [wPokedexDescriptionTextState]
	cp POKEDEX_DESCRIPTION_TEXT_CATEGORY
	jr nz, .render_next
	call PokedexSelectedMon_AdvanceDescriptionTextSource
	ld a, [wPokedexDescriptionTextSource]
	add 4
	ld [wPokedexDescriptionTextSource], a
	jr nc, .category_skipped
	ld a, [wPokedexDescriptionTextSource + 1]
	inc a
	ld [wPokedexDescriptionTextSource + 1], a
.category_skipped
	ld a, [wPokedexDescriptionTextPage]
	and a
	ld a, POKEDEX_DESCRIPTION_TEXT_SKIP_PAGE
	jr nz, .state
	ld a, POKEDEX_DESCRIPTION_TEXT_RENDER
.state
	ld [wPokedexDescriptionTextState], a
	ret
.render_next
	ld a, POKEDEX_DESCRIPTION_TEXT_RENDER
	ld [wPokedexDescriptionTextState], a
	jr .save_source
.render
	ld a, [bc]
	inc bc
	cp '@'
	jr z, .ready
	cp '<NEXT>'
	jr z, .next_line
	cp '#'
	jr z, .pokemon
	ld [hli], a
	ld [de], a
	inc de
.check_end
	ld a, c
	cp LOW(wPokedexDescriptionTextChunk + POKEDEX_DESCRIPTION_TEXT_CHUNK)
	jr nz, .next
.save_source
	call PokedexSelectedMon_AdvanceDescriptionTextSource
	; fallthrough

PokedexSelectedMon_SaveDescriptionTextCursor:
	ld a, l
	ld [wPokedexDescriptionTextCursor], a
	ld a, h
	ld [wPokedexDescriptionTextCursor + 1], a
	ld a, e
	ld [wPokedexDescriptionTextOwnerCursor], a
	ld a, d
	ld [wPokedexDescriptionTextOwnerCursor + 1], a
	ret

PokedexSelectedMon_RenderDescriptionTextChunk.next_line:
	ld a, [wPokedexDescriptionTextRow]
	inc a
	ld [wPokedexDescriptionTextRow], a
	hlcoord 2, 12
	ld de, wPokedexOwnerTilemapBuffer + 12 * TILEMAP_WIDTH + 2
	dec a
	jr z, .line_ready
	hlcoord 2, 14
	ld de, wPokedexOwnerTilemapBuffer + 14 * TILEMAP_WIDTH + 2
.line_ready
	jr PokedexSelectedMon_RenderDescriptionTextChunk.check_end

PokedexSelectedMon_RenderDescriptionTextChunk.pokemon:
FOR glyph, 0, 4
	ld a, [PlacePOKeText + glyph]
	ld [hli], a
	ld [de], a
	inc de
ENDR
	jr PokedexSelectedMon_RenderDescriptionTextChunk.check_end

PokedexSelectedMon_RenderDescriptionTextChunk.ready:
; The lower padded rows are immutable until VBlank acknowledges this request.
	ld a, POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT
	ld [wPokedexOwnerTransition], a
	ldh a, [hVBlank]
	or VBLANK_POKEDEX
	ldh [hVBlank], a
	ret

PokedexSelectedMon_AdvanceDescriptionTextSource:
	push hl
	ld a, c
	sub LOW(wPokedexDescriptionTextChunk)
	ld hl, wPokedexDescriptionTextSource
	add [hl]
	ld [hli], a
	jr nc, .done
	inc [hl]
.done
	pop hl
	ret
