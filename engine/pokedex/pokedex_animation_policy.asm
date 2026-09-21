; Selected-only scheduling policy. See docs/pokedex_animation_scheduler.md.
; Called in mainline with IME enabled; bank and register ownership matter.

Pokedex_ChooseAnimationWork::
	ldh a, [hVBlankCounter]
	ld b, a
	ld a, [wPokedexAnimWorkTick]
	cp b
	jr z, .idle
	ld a, [wPokedexAnimFlags]
	and POKEDEX_ANIM_STAGE_WORK_MASK
	cp 1 << POKEDEX_ANIM_STAGE_VALID_F
	jr nz, .decode
	ld a, [wPokedexAnimStageTileCount]
	ld b, a
	ld a, [wPokedexAnimUploadOffset]
	cp b
	jr nc, .decode
	ld e, a
	ld d, 0
	ld hl, POKEDEX_ANIM_SOURCE_TILES
	add hl, de
	ld a, [wPokedexAnimDictionaryTilesRemaining]
	ld b, a
	ld a, [wPokedexAnimDictionaryTileCount]
	sub b
	cp [hl]
	jr c, .decode
	jr z, .decode
	ld a, POKEDEX_ANIM_WORK_UPLOAD
	jr .record
.decode
	call Pokedex_AnimationDictionaryBelowTarget
	jr nc, .idle
	ld a, POKEDEX_ANIM_WORK_DECODE
.record
	ld c, a
	ldh a, [hVBlankCounter]
	ld [wPokedexAnimWorkTick], a
	ld a, c
	ret
.idle
	xor a
	ret

Pokedex_BeginOwnerLoop::
	ldh a, [hVBlankCounter]
	ld [wPokedexAnimLoopTick], a
	ld hl, wPokedexAnimSchedulerControl
	res POKEDEX_ANIM_FINISH_USED_F, [hl]
	jp JoyTextDelay

Pokedex_EndOwnerLoop::
	ldh a, [hVBlank]
	bit VBLANK_DEX_QUIET_F, a
	jp z, DelayFrame
	ld hl, wPokedexAnimSchedulerControl
	bit POKEDEX_ANIM_AUDIO_DUE_F, [hl]
	jr z, .audio_done
	res POKEDEX_ANIM_AUDIO_DUE_F, [hl]
	call ServiceSampledCryAsync
.audio_done
	; Arm before reading the clock: a VBlank during the comparison must stay seen.
	ld a, 1
	ld [wVBlankOccurred], a
	ldh a, [hVBlankCounter]
	ld b, a
	ld a, [wPokedexAnimLoopTick]
	cp b
	jr nz, .returned_to_owner
.wait
	halt
	nop
	ld a, [wVBlankOccurred]
	and a
	jr nz, .wait
.returned_to_owner
	ld hl, wPokedexAnimSchedulerControl
	set POKEDEX_ANIM_AUDIO_DUE_F, [hl]
	ret

Pokedex_AcquireQuietAnimationOwner::
; Caller: Selected reveal has already published empty OAM and the viewport.
; Fail closed if competing requests or unpublished viewport values remain.
	ldh a, [hVBlank]
	and 7
	jr z, .check_requests
	cp VBLANK_POKEDEX
	ret nz
.check_requests
; Cancellation may leave the idle Dex handler selected, but not a live map.
	ld a, [wPokedexAnimFlags]
	and (1 << POKEDEX_ANIM_MAP_PENDING_F) | (1 << POKEDEX_ANIM_MAP_PUBLISHED_F)
	ret nz
	ldh a, [hBGMapUpdate]
	ld b, a
	ldh a, [hCGBPalUpdate]
	or b
	ld b, a
	ldh a, [hDMATransfer]
	or b
	ld b, a
	ldh a, [hBGMapMode]
	or b
	ld b, a
	ldh a, [hMapAnims]
	or b
	ld b, a
	ld a, [wRequested1bppSize]
	or b
	ld b, a
	ld a, [wRequested2bppSize]
	or b
	ld b, a
	ld a, [wPokedexOwnerTransition]
	or b
	ret nz
	FOR port, 0, 4
		IF port == 0
			ldh a, [hSCX]
			ld b, a
			ldh a, [rSCX]
		ELIF port == 1
			ldh a, [hSCY]
			ld b, a
			ldh a, [rSCY]
		ELIF port == 2
			ldh a, [hWY]
			ld b, a
			ldh a, [rWY]
		ELSE
			ldh a, [hWX]
			ld b, a
			ldh a, [rWX]
		ENDC
		cp b
		ret nz
	ENDR
	xor a
	ld [wPokedexAnimSchedulerControl], a
	ldh a, [hVBlankCounter]
	dec a
	ld [wPokedexAnimWorkTick], a
	ld a, 1
	ldh [hOAMUpdate], a
	ld a, 1 << VBLANK_DEX_QUIET_F
	ldh [hVBlank], a
	ret

Pokedex_ReleaseQuietAnimationOwner::
	ldh a, [hVBlank]
	bit VBLANK_DEX_QUIET_F, a
	ret z
	and 7
	ldh [hVBlank], a
	xor a
	ldh [hOAMUpdate], a
	ld [wPokedexAnimSchedulerControl], a
	ret

Pokedex_TryFinishAnimationStage::
; One optional complete remainder, never an unbounded catch-up loop.
	ldh a, [hVBlank]
	bit VBLANK_DEX_QUIET_F, a
	ret z
	ld hl, wPokedexAnimSchedulerControl
	bit POKEDEX_ANIM_FINISH_USED_F, [hl]
	ret nz
	ld a, [wPokedexAnimPlaybackState]
	cp POKEDEX_ANIM_PLAYBACK_PLAYING
	ret nz
	ld a, [wPokedexAnimFlags]
	and POKEDEX_ANIM_STAGE_WORK_MASK
	cp 1 << POKEDEX_ANIM_STAGE_VALID_F
	ret nz
	ld a, [wPokedexAnimDisplaySlot]
	ld b, a
	ld a, [wPokedexAnimStageSlot]
	cp b
	ret z
	ld a, [wPokedexAnimUploadOffset]
	ld b, a
	ld a, [wPokedexAnimStageTileCount]
	sub b
	ret z
	ret c
	cp POKEDEX_ANIM_UPLOAD_CHUNK_TILES + 1
	ret nc
	ld d, a
; Generated plans guarantee nondecreasing source IDs; check the final source.
	ld a, [wPokedexAnimStageTileCount]
	dec a
	ld e, a
	ld hl, POKEDEX_ANIM_SOURCE_TILES
	push de
	ld d, 0
	add hl, de
	pop de
	ld a, [wPokedexAnimDictionaryTilesRemaining]
	ld b, a
	ld a, [wPokedexAnimDictionaryTileCount]
	sub b
	cp [hl]
	ret c
	ret z
	call Pokedex_AdmitAnimationFinish
	ret nc
	ld hl, wPokedexAnimSchedulerControl
	set POKEDEX_ANIM_FINISH_USED_F, [hl]
	call Pokedex_ServiceAnimationUploadChunk
	jp Pokedex_CommitDescriptionAnimation

Pokedex_AdmitAnimationFinish::
; d = complete ready remainder, 1..20. IME must be enabled by caller contract.
; These exact hardware checks intentionally reject unmodeled timer settings.
	ldh a, [rKEY1]
	bit 7, a
	jr nz, .reject
	ldh a, [hLCDCPointer]
	and a
	jr nz, .reject
	ldh a, [rLCDC]
	bit 7, a
	jr z, .reject
	ldh a, [rTAC]
	and 7
	bit 2, a
	jr z, .timer_off
	cp 6
	jr z, .fast_timer
	cp 4
	jr nz, .reject
	ldh a, [rTMA]
	and a
	jr nz, .reject
	ldh a, [hSampledCryTimer]
	and a
	jr nz, .reject
	ld e, 20
	jr .time_gate
.fast_timer
	ldh a, [rTMA]
	cp 57
	jr nc, .reject
	ldh a, [hSampledCryTimer]
	and a
	ld e, 20
	jr z, .time_gate
	ldh a, [rTMA]
	cp 56
	jr nz, .reject
	call Pokedex_CheckAnimationAudioRunway
	jr nc, .reject
	ld e, 40
	jr .time_gate
.timer_off
	ldh a, [hSampledCryTimer]
	and a
	jr nz, .reject
	ld e, 0
.time_gate
; Compute threshold before sampling the coarse hardware clock.
	ld a, d
	dec a
	add e
	ld e, a
	ld d, 0
	ld hl, Pokedex_AnimationFinishLatestLY
	add hl, de
	ld b, [hl]
	ldh a, [hVBlankCounter]
	inc a
	ld c, a
	ld a, [wPokedexAnimDeadline]
	sub c
	bit 7, a
	jr nz, .reject
	ldh a, [rSTAT]
	and 3
	cp 1
	jr z, .reject
	ldh a, [rLY]
	cp b
	ret
.reject
	and a
	ret

Pokedex_CheckAnimationAudioRunway::
; Return carry for enough cached blocks. Read shared counters with timer masked
; briefly, restore the caller's bank, then reopen interrupts before the LY gate.
	ld a, d
	dec a
	ld e, a
	push de
	ld d, 0
	ld hl, Pokedex_AnimationFinishAudioMinimum
	add hl, de
	ld c, [hl]
	ldh a, [rSVBK]
	push af
	ld a, BANK(wSampledCryCacheCount)
	ldh [rSVBK], a
	di
	ld a, [wSampledCryBlockPeriod]
	cp 200
	jr nz, .bad_period
	ldh a, [hSampledCryBlocks + 1]
	and a
	jr nz, .full_reserve
	ldh a, [hSampledCryBlocks]
	cp c
	jr nc, .full_reserve
	ld c, a
.full_reserve
	ld a, [wSampledCryCacheCount]
	cp c
	ccf
	jr .restore
.bad_period
	and a
.restore
	ld a, 0
	rla
	ld c, a
	pop af
	ldh [rSVBK], a
	pop de
	ei
	nop
	ld a, c
	rrca
	ret


; Conservative bounds generated and checked by tools/dex_timing/finish_bounds.py.
; Three 20-entry LY rows: timer off, inactive short timer, active sampled timer.
Pokedex_AnimationFinishLatestLY::
	db 87, 83, 80, 77, 73, 70, 67, 64, 60, 57, 54, 51, 47, 44, 41, 37, 34, 31, 28, 24
	db 86, 83, 79, 76, 73, 70, 66, 63, 59, 56, 53, 50, 46, 43, 40, 36, 33, 30, 26, 23
	db 78, 75, 72, 64, 61, 57, 54, 51, 48, 44, 37, 34, 30, 27, 24, 20, 17, 14, 6, 3
Pokedex_AnimationFinishAudioMinimum::
	db 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 16, 17, 17
ASSERT Pokedex_AnimationFinishAudioMinimum - Pokedex_AnimationFinishLatestLY == 3 * POKEDEX_ANIM_UPLOAD_CHUNK_TILES
ASSERT @ - Pokedex_AnimationFinishAudioMinimum == POKEDEX_ANIM_UPLOAD_CHUNK_TILES
