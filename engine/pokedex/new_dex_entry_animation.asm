SECTION "New Dex Entry Animation", ROMX

DEF NEW_DEX_ANIM_ACTIVE_F EQU 0
DEF NEW_DEX_ANIM_READY_F  EQU 1
DEF NEW_DEX_ANIM_FINISH_F EQU 2
DEF NEW_DEX_ANIM_FIRST_F  EQU 3
DEF NEW_DEX_ANIM_ACK_F    EQU 4
DEF NEW_DEX_ANIM_MISSED_F EQU 5 ; instrumentation: one report per deadline
DEF NEW_DEX_ANIM_TEXT_F   EQU 6 ; complete description waiting for publication

DEF NEW_DEX_ANIM_NOT_READY EQU 1
DEF NEW_DEX_ANIM_LATE      EQU 2
DEF NEW_DEX_ANIM_WINDOW    EQU 3

DEF NEW_DEX_ENTRY_PICTURE_MAP_OFFSET EQU TILEMAP_WIDTH + 1
ASSERT HIGH(vBGMap0 + NEW_DEX_ENTRY_PICTURE_MAP_OFFSET) == HIGH(vBGMap0 + NEW_DEX_ENTRY_PICTURE_MAP_OFFSET + 6 * TILEMAP_WIDTH + 6)
ASSERT BANK(wNewDexEntryAnimPairs) == BANK(wPokeAnimStruct)
ASSERT BANK(wNewDexEntryAnimMap) == BANK(wPokeAnimStruct)
ASSERT 2 * 7 * 7 <= SCREEN_AREA

NewDexEntry_AnimationStep::
; Foreground only. The caller waits through DelayFrame after this returns.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokeAnimStruct)
	ldh [rSVBK], a
	ld a, [wNewDexEntryAnimFlags]
	and a
	call z, NewDexEntry_InitializeAnimation
	pop af
	ldh [rSVBK], a
	ret

NewDexEntry_InitializeAnimation:
	decoord 1, 1
	farcall PokeAnim_InitDexFrameProducer
	ld a, e
	ld [wNewDexEntryAnimTimeline], a
	ld a, d
	ld [wNewDexEntryAnimTimeline + 1], a
	ld b, c
	xor a
.square
	add c
	dec b
	jr nz, .square
	ld [wNewDexEntryAnimBaseCount], a
	ldh a, [hVBlank]
	ld [wNewDexEntryAnimSavedVBlank], a
	ldh a, [hOAMUpdate]
	ld [wNewDexEntryAnimSavedOAM], a
	ld a, 1 << NEW_DEX_ANIM_ACTIVE_F | 1 << NEW_DEX_ANIM_FIRST_F
	ld [wNewDexEntryAnimFlags], a
	call NewDexEntry_BuildAnimationMap
	ld a, [wPokeAnimSpecies]
	call PlayMonCry2
; Arm only after preparation and synchronous cry startup have finished.
	ldh a, [hVBlankCounter]
	inc a
	ld [wNewDexEntryAnimDeadline], a
	xor a
	ldh [hBGMapMode], a
	ld a, 1
	ldh [hOAMUpdate], a
	ld a, VBLANK_NEW_DEX_ENTRY
	ldh [hVBlank], a
	ret

NewDexEntry_ServiceAnimation::
; DelayFrame calls this after audio service, including inside WaitBGMap.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokeAnimStruct)
	ldh [rSVBK], a
	ld hl, wNewDexEntryAnimFlags
	bit NEW_DEX_ANIM_ACK_F, [hl]
	jr z, .build
.ack
	ld hl, wNewDexEntryAnimMap
	decoord 1, 1
	call NewDexEntry_CopyBackingMap
	ld a, [wNewDexEntryAnimFlags]
	and 1 << NEW_DEX_ANIM_FIRST_F | 1 << NEW_DEX_ANIM_FINISH_F
	jr z, .backed
	ld a, 1 | BG_BANK1
	ld hl, wNewDexEntryAnimFlags
	bit NEW_DEX_ANIM_FINISH_F, [hl]
	jr z, .attr
	ld a, 1
.attr
	res NEW_DEX_ANIM_FIRST_F, [hl]
	decoord 1, 1, wAttrmap
	call NewDexEntry_FillBackingAttrs
.backed
	ld hl, wNewDexEntryAnimFlags
	res NEW_DEX_ANIM_ACK_F, [hl]
	bit NEW_DEX_ANIM_FINISH_F, [hl]
	jr nz, .complete
.build
	ld a, [wNewDexEntryAnimFlags]
; Publication may have interrupted the earlier ACK check. Do not reuse its
; map until acknowledged; test ACK and READY from the same flag snapshot.
	bit NEW_DEX_ANIM_ACK_F, a
	jr nz, .ack
	bit NEW_DEX_ANIM_READY_F, a
	jr nz, .return
	bit NEW_DEX_ANIM_ACTIVE_F, a
	call nz, NewDexEntry_BuildAnimationMap
.return
	pop af
	ldh [rSVBK], a
	ret
.complete
; Keep the owner until a queued description has reached VRAM. Preserve the
; final ACK so the next service can finish normally after the text copy.
	bit NEW_DEX_ANIM_TEXT_F, [hl]
	jr z, .restore
	set NEW_DEX_ANIM_ACK_F, [hl]
	jr .return
.restore
	call NewDexEntry_RestoreAnimationOwner
NewDexEntry_AnimationCompleted::
	jr NewDexEntry_ServiceAnimation.return

NewDexEntry_ReadAnimationEvent:
	ld a, [wNewDexEntryAnimTimeline]
	ld l, a
	ld a, [wNewDexEntryAnimTimeline + 1]
	ld h, a
.read
	ld a, BANK(DexAnimationTimelinePointers)
	call GetFarByte
	inc hl
	cp POKEDEX_ANIM_TIMELINE_FINISH
	jr z, .finish
	cp POKEDEX_ANIM_TIMELINE_LOOP
	jr z, .loop
	ld b, a
	and $f
	jr nz, .duration
	ld a, BANK(DexAnimationTimelinePointers)
	call GetFarByte
	inc hl
.duration
	ld [wNewDexEntryAnimDuration], a
	ld a, b
	swap a
	and $f
	ld [wNewDexEntryAnimFrameID], a
	inc hl ; high-water target is only needed by the streaming owner
.save
	ld a, l
	ld [wNewDexEntryAnimTimeline], a
	ld a, h
	ld [wNewDexEntryAnimTimeline + 1], a
	ret
.finish
	xor a
	ld [wNewDexEntryAnimFrameID], a
	ld [wNewDexEntryAnimDuration], a
	ld a, [wNewDexEntryAnimFlags]
	or 1 << NEW_DEX_ANIM_FINISH_F
	ld [wNewDexEntryAnimFlags], a
	jr .save
.loop
	push hl
	ld a, BANK(DexAnimationTimelinePointers)
	call GetFarWord
	ld d, h
	ld e, l
	pop hl
	inc hl
	inc hl
	ld a, l
	sub e
	ld l, a
	ld a, h
	sbc d
	ld h, a
	jr .read

NewDexEntry_BuildAnimationMap::
	call NewDexEntry_ReadAnimationEvent
	ld hl, NewDexEntry_BaseAnimationMap
	ld de, wNewDexEntryAnimMap
	ld bc, 7 * 7
	call CopyBytes
	ld a, [wNewDexEntryAnimFrameID]
	and a
	jr z, .ready
	ld b, a
	farcall PokeAnim_GetDexFramePlanPointer
	ld a, d
	call GetFarByte
	and a
	jr z, .ready
	push af
	inc hl
	inc hl
	add a
	ld c, a
	ld b, 0
	ld a, d
	ld de, wNewDexEntryAnimPairs
	call FarCopyBytes
	pop af
	ld b, a
	ld hl, wNewDexEntryAnimPairs
.pair
	ld a, [hli]
	ld c, a
	and $7f
	add LOW(wNewDexEntryAnimMap)
	ld e, a
	ld a, HIGH(wNewDexEntryAnimMap)
	adc 0
	ld d, a
	ld a, [hli]
	bit 7, c
	jr nz, .store
; Tail sources follow the native square, but resident VRAM has a padded base.
	ld c, a
	ld a, [wNewDexEntryAnimBaseCount]
	cpl
	inc a
	add c
	add 7 * 7
	cp $7f
	jr c, .store
	inc a ; the resident loader skips tile $7f
.store
	ld [de], a
	dec b
	jr nz, .pair
.ready
NewDexEntry_AnimationPrepared::
	ld hl, wNewDexEntryAnimFlags
	set NEW_DEX_ANIM_READY_F, [hl]
	ret

NewDexEntry_PublishAnimation::
; Interrupt only. Return a != 0 if this interval's graphics budget was used.
	ldh a, [rSVBK]
	push af
	ldh a, [rVBK]
	push af
	ld a, BANK(wPokeAnimStruct)
	ldh [rSVBK], a
	ldh a, [rLY]
	cp 144
	jr c, .check_deadline
	cp 153
	jr nc, .check_deadline
	xor a
	ldh [rVBK], a
	ld a, [wTilemap + 17 * SCREEN_WIDTH + 18]
	ld [vBGMap0 + 17 * TILEMAP_WIDTH + 18], a
.check_deadline
	ld a, [wNewDexEntryAnimFlags]
	bit NEW_DEX_ANIM_ACTIVE_F, a
	jp z, NewDexEntry_NoAnimationPublication
	and 1 << NEW_DEX_ANIM_FINISH_F | 1 << NEW_DEX_ANIM_ACK_F
	cp 1 << NEW_DEX_ANIM_FINISH_F | 1 << NEW_DEX_ANIM_ACK_F
	jp z, NewDexEntry_NoAnimationPublication
	ldh a, [hVBlankCounter]
	ld b, a
	ld a, [wNewDexEntryAnimDeadline]
	sub b
	jr z, .due
	bit 7, a
	jp z, NewDexEntry_NoAnimationPublication
	ld a, NEW_DEX_ANIM_LATE
	call NewDexEntry_RecordAnimationMiss
.due
	ld a, [wNewDexEntryAnimFlags]
	bit NEW_DEX_ANIM_READY_F, a
	jr nz, .ready
	ld a, NEW_DEX_ANIM_NOT_READY
	call NewDexEntry_RecordAnimationMiss
	jp NewDexEntry_NoAnimationPublication
.ready
; Fully unrolled first/final copies finish their VRAM writes within 1,708 T
; of the LY read. Even the end of LY 149 leaves at least 1,824 T available.
	ld b, 150
.cutoff
	ldh a, [rLY]
	cp 144
	jr c, .late_window
	cp b
	jr c, .copy
.late_window
	ld a, NEW_DEX_ANIM_WINDOW
	call NewDexEntry_RecordAnimationMiss
	jp NewDexEntry_NoAnimationPublication
.copy
	xor a
	ldh [rVBK], a
	ld hl, wNewDexEntryAnimMap
	ld de, vBGMap0 + NEW_DEX_ENTRY_PICTURE_MAP_OFFSET
	call NewDexEntry_CopyVRAMMap
	ld a, [wNewDexEntryAnimFlags]
	and 1 << NEW_DEX_ANIM_FIRST_F | 1 << NEW_DEX_ANIM_FINISH_F
	jr z, .published
	ld a, 1
	ldh [rVBK], a
	ld a, [wNewDexEntryAnimFlags]
	bit NEW_DEX_ANIM_FINISH_F, a
	ld a, 1 | BG_BANK1
	jr z, .attr
	ld a, 1
.attr
	ld de, vBGMap0 + NEW_DEX_ENTRY_PICTURE_MAP_OFFSET
	call NewDexEntry_FillVRAMAttrs
.published
; Advance the authored deadline here, atomically with publication. A delayed
; foreground acknowledgement cannot postpone or conceal the next deadline.
	ld a, [wNewDexEntryAnimDuration]
	ld hl, wNewDexEntryAnimDeadline
	add [hl]
	ld [hl], a
	ld hl, wNewDexEntryAnimPublications
	inc [hl]
	ld hl, wNewDexEntryAnimFlags
	res NEW_DEX_ANIM_READY_F, [hl]
	res NEW_DEX_ANIM_MISSED_F, [hl]
	set NEW_DEX_ANIM_ACK_F, [hl]
NewDexEntry_AnimationPublished::
	call NewDexEntry_TryPublishDescription
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ld a, 1
	ret

NewDexEntry_NoAnimationPublication:
; Text is disjoint from the picture and may publish even while its ACK waits.
	call NewDexEntry_TryPublishDescription
	ld b, a
; A publication can interrupt description drawing before DelayFrame runs.
; Do not let UpdateBGMap copy the old or partially synchronized backing map.
	ld a, [wNewDexEntryAnimFlags]
	and 1 << NEW_DEX_ANIM_ACK_F
	or b
	ld b, a
	pop af
	ldh [rVBK], a
	pop af
	ldh [rSVBK], a
	ld a, b
	ret

NewDexEntry_RecordAnimationMiss:
; INSTRUMENTATION: latched once per missed deadline. No padding allocation.
; a = 1 not ready, 2 late deadline, 3 unsafe VBlank window.
	push hl
	ld hl, wNewDexEntryAnimFlags
	bit NEW_DEX_ANIM_MISSED_F, [hl]
	jr nz, .done
	set NEW_DEX_ANIM_MISSED_F, [hl]
	ld [wNewDexEntryAnimMissReason], a
	ld hl, wNewDexEntryAnimMisses
NewDexEntryAnimationMiss::
	inc [hl]
	pop hl
	ret
NewDexEntry_RecordAnimationMiss.done:
	pop hl
	ret

MACRO new_dex_entry_copy_rows
	ld b, 7
.row\@
	REPT 7
		ld a, [hli]
		ld [de], a
		IF \1 == TILEMAP_WIDTH
			inc e ; the seven cells never cross a VRAM row's low-byte boundary
		ELSE
			inc de
		ENDC
	ENDR
	ld a, e
	add \1 - 7
	ld e, a
	jr nc, .carry\@
	inc d
.carry\@
	dec b
	jr nz, .row\@
	ret
ENDM
NewDexEntry_CopyBackingMap:
	new_dex_entry_copy_rows SCREEN_WIDTH
NewDexEntry_CopyVRAMMap:
; VBlank-only fixed destination. All seven rows stay in the same high byte.
	FOR row, 7
		REPT 6
			ld a, [hli]
			ld [de], a
			inc e
		ENDR
		ld a, [hli]
		ld [de], a
		IF row < 6
			ld e, LOW(vBGMap0 + NEW_DEX_ENTRY_PICTURE_MAP_OFFSET + (row + 1) * TILEMAP_WIDTH)
		ENDC
	ENDR
	ret

MACRO new_dex_entry_fill_rows
	ld c, a
	ld b, 7
.row\@
	ld a, c
	REPT 7
		ld [de], a
		IF \1 == TILEMAP_WIDTH
			inc e
		ELSE
			inc de
		ENDC
	ENDR
	ld a, e
	add \1 - 7
	ld e, a
	jr nc, .carry\@
	inc d
.carry\@
	dec b
	jr nz, .row\@
	ret
ENDM
NewDexEntry_FillBackingAttrs:
	new_dex_entry_fill_rows SCREEN_WIDTH
NewDexEntry_FillVRAMAttrs:
; The publisher does not need its old source HL after copying the map.
	ld h, d
	ld l, e
	FOR row, 7
		REPT 7
			ld [hli], a
		ENDR
		IF row < 6
			ld l, LOW(vBGMap0 + NEW_DEX_ENTRY_PICTURE_MAP_OFFSET + (row + 1) * TILEMAP_WIDTH)
		ENDC
	ENDR
	ret

NewDexEntry_RestoreAnimationOwner:
	ld a, [wNewDexEntryAnimSavedVBlank]
	ldh [hVBlank], a
	ld a, [wNewDexEntryAnimSavedOAM]
	ldh [hOAMUpdate], a
	xor a
	ld [wNewDexEntryAnimFlags], a
	ld [wFrameCounter], a
	ret

NewDexEntry_CancelAnimation::
	xor a
	ld [wFrameCounter], a
	ldh a, [hVBlank]
	cp VBLANK_NEW_DEX_ENTRY
	ret nz
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokeAnimStruct)
	ldh [rSVBK], a
	call NewDexEntry_RestoreAnimationOwner
	pop af
	ldh [rSVBK], a
	ret

NewDexEntry_BaseAnimationMap:
	FOR y, 7
		FOR x, 7
			db x * 7 + y
		ENDR
	ENDR

DEF NEW_DEX_ENTRY_UPLOAD_TILES EQU 32
ASSERT sNewDexEntryUploadBuffer >= sPaddedEnemyFrontPic + 49 tiles
ASSERT sNewDexEntryUploadBuffer + NEW_DEX_ENTRY_UPLOAD_TILES tiles <= sScratch + $60 tiles
ASSERT LOW(sNewDexEntryUploadBuffer) & $f == 0

NewDexEntry_UploadTiles::
; Registration-local source in open SRAM or selected WRAM, destination hl.
; Up to 32 aligned tiles per queued VBlank GDMA; normal audio/joypad still run.
.next
	ld a, c
	cp 2
	jp c, Get2bpp
	cp NEW_DEX_ENTRY_UPLOAD_TILES
	jr c, .chunk
	ld a, NEW_DEX_ENTRY_UPLOAD_TILES
.chunk
	ld b, a
	push bc
	push de
	push hl
	ld a, e
	and $f
	jr z, .aligned
; sPaddedEnemyFrontPic starts at $a001; GDMA would round that address down.
	push bc
	push hl
	ld h, d
	ld l, e
	ld de, sNewDexEntryUploadBuffer
	ld c, b
	ld b, 0
	REPT 4
		sla c
		rl b
	ENDR
	call CopyBytes
	ld de, sNewDexEntryUploadBuffer
	pop hl
	pop bc
.aligned
	ld a, d
	ldh [rHDMA1], a
	ld a, e
	ldh [rHDMA2], a
	ld a, h
	and $1f
	ldh [rHDMA3], a
	ld a, l
	ldh [rHDMA4], a
	ld a, b
	dec a
	ldh [hDMATransfer], a
	farcall WaitDMATransfer
	pop hl
	pop de
	pop bc
	ld a, c
	sub b
	push af
	ld c, b
	ld b, 0
	REPT 4
		sla c
		rl b
	ENDR
	add hl, bc
	ld a, e
	add c
	ld e, a
	ld a, d
	adc b
	ld d, a
	pop af
	ld c, a
	and a
	jr nz, .next
	ret

NewDexEntry_DisplayPage2::
; Only description text changes. Keep foreground map service available while
; skipping page 1, without repeating header, dimensions or first-page drawing.
	call ServiceSampledCryAsync
	call .ServiceAnimation
	xor a
	ldh [hBGMapMode], a
	ld a, [wTempSpecies]
	ld b, a
	farcall GetDexEntryPointer
	ld h, d
	ld l, e
.category
	ld a, b
	call GetFarByte
	inc hl
	cp '@'
	jr nz, .category
	REPT 4 ; height and weight
		inc hl
	ENDR
.page1
	ld a, b
	call GetFarByte
	inc hl
	cp '@'
	jr nz, .page1
	call .ServiceAnimation
	push bc
	push hl
	lb bc, 5, SCREEN_WIDTH - 2
	hlcoord 2, 10
	call ClearBox
	ld a, $58 ; page 2
	ld [wTilemap + 9 * SCREEN_WIDTH + 2], a
	pop de
	pop bc
	ld a, b
	hlcoord 2, 10
	call PlaceFarString
	call .ServiceAnimation
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokeAnimStruct)
	ldh [rSVBK], a
	ldh a, [hVBlank]
	cp VBLANK_NEW_DEX_ENTRY
	jr z, .queue
; If playback already ended, borrow the same owner just for the text commit.
	ld [wNewDexEntryAnimSavedVBlank], a
	ldh a, [hOAMUpdate]
	ld [wNewDexEntryAnimSavedOAM], a
	ld a, 1
	ldh [hOAMUpdate], a
	ld a, VBLANK_NEW_DEX_ENTRY
	ldh [hVBlank], a
.queue
	ld hl, wNewDexEntryAnimFlags
.description_ready ; instrumentation boundary: all source cells are complete
	set NEW_DEX_ANIM_TEXT_F, [hl]
.wait_description
	call DelayFrame
	ld hl, wNewDexEntryAnimFlags
	bit NEW_DEX_ANIM_TEXT_F, [hl]
	jr nz, .wait_description
	ldh a, [hVBlank]
	cp VBLANK_NEW_DEX_ENTRY
	jr nz, .description_done
	bit NEW_DEX_ANIM_ACTIVE_F, [hl]
	call z, NewDexEntry_RestoreAnimationOwner
.description_done
	ld a, 1
	ldh [hBGMapMode], a
	pop af
	ldh [rSVBK], a
	ret

.ServiceAnimation:
; Preserve the text pointer and bank; audio retains its DelayFrame refills.
	push af
	ldh a, [hVBlank]
	cp VBLANK_NEW_DEX_ENTRY
	jr nz, .done
	push bc
	push de
	push hl
	farcall NewDexEntry_ServiceAnimation
	pop hl
	pop de
	pop bc
.done
	pop af
	ret

NewDexEntry_TryPublishDescription:
; Interrupt only, WRAM bank 2 selected, caller restores VBK. Animation has
; already had first claim on the interval; recheck the remaining live budget.
	ld hl, wNewDexEntryAnimFlags
	bit NEW_DEX_ANIM_TEXT_F, [hl]
	jp z, .none
.cutoff
	ldh a, [rLY]
	cp 144
	jp c, .none
	cp 149
	jp nc, .none
	xor a
	ldh [rVBK], a
	ld de, vBGMap0 + 10 * TILEMAP_WIDTH + 2
	FOR row, 10, 15
		ld hl, wTilemap + row * SCREEN_WIDTH + 2
		REPT SCREEN_WIDTH - 3
			ld a, [hli]
			ld [de], a
			inc e
		ENDR
		ld a, [hli]
		ld [de], a
		IF row < 14
			ld e, LOW(vBGMap0 + (row + 1) * TILEMAP_WIDTH + 2)
		ENDC
	ENDR
ASSERT HIGH(vBGMap0 + 10 * TILEMAP_WIDTH + 2) == HIGH(vBGMap0 + 14 * TILEMAP_WIDTH + SCREEN_WIDTH - 1)
	ld a, [wTilemap + 9 * SCREEN_WIDTH + 2]
	ld [vBGMap0 + 9 * TILEMAP_WIDTH + 2], a
	ld hl, wNewDexEntryAnimFlags
	res NEW_DEX_ANIM_TEXT_F, [hl]
NewDexEntry_DescriptionPublished:: ; instrumentation: last store and ACK complete
	ld a, 1
	ret
NewDexEntry_TryPublishDescription.none:
	xor a
	ret
