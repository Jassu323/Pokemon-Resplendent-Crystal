SECTION "Dex Animation Timeline Reader", ROMX, BANK[$a5]

Pokedex_ReadNextAnimationEvent::
; This routine must execute in the same bank as the generated timelines.
	ld a, [wPokedexAnimTimelineAddress]
	ld l, a
	ld a, [wPokedexAnimTimelineAddress + 1]
	ld h, a

.read
	ld a, [hli]
	cp POKEDEX_ANIM_TIMELINE_FINISH
	jr z, .finish
	cp POKEDEX_ANIM_TIMELINE_LOOP
	jr z, .loop
	ld b, a
	and $f
	jr nz, .got_duration
	ld a, [hli]
.got_duration
	ld c, a
	ld a, b
	swap a
	and $f
	ld b, a
	ld a, [hli]
	ld d, a
	ld a, l
	ld [wPokedexAnimTimelineAddress], a
	ld a, h
	ld [wPokedexAnimTimelineAddress + 1], a
	ld a, c
	ld [wPokedexAnimStageDuration], a
	ld a, b
	ld [wPokedexAnimStageFrameID], a
	ld a, d
	ld [wPokedexAnimDictionaryTarget], a
	ld hl, wPokedexAnimDebugEventReads
	inc [hl]
	ret

.loop
	ld e, [hl]
	inc hl
	ld d, [hl]
	inc hl
	ld a, l
	sub e
	ld l, a
	ld a, h
	sbc d
	ld h, a
	jr .read

.finish
	ld a, l
	ld [wPokedexAnimTimelineAddress], a
	ld a, h
	ld [wPokedexAnimTimelineAddress + 1], a
	xor a
	ld [wPokedexAnimStageDuration], a
	ld [wPokedexAnimStageFrameID], a
	ld [wPokedexAnimDictionaryTarget], a
	ld hl, wPokedexAnimFlags
	set POKEDEX_ANIM_ENDED_F, [hl]
	ld hl, wPokedexAnimDebugEventReads
	inc [hl]
	ret
