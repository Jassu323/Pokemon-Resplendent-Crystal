; COST-ONLY DESIGN DRAFT. Not included by main.asm or the game Makefile.
; This is not a tested replacement for the linked scheduler. The host report
; measures its sections and selected CPU-only contracts before integration.
INCLUDE "linked.inc"

DEF QUIET_OWNER EQU $80
DEF AUDIO_DUE EQU 0
DEF FINISH_USED EQU 1
DEF wPolicyLoopTick EQU wPokedexAnimScheduleAddress
DEF wPolicyWorkTick EQU wPokedexAnimScheduleAddress + 1
DEF wPolicyControl EQU wPokedexAnimScheduleRun
DEF SOURCES EQU wPokedexWRAM0Scratch + $460

SECTION "Cost-only owner policy", ROMX[$7400], BANK[$a0]

Cost_ActionStart::
PolicyChooseAction::
	ldh a, [hVBlankCounter]
	ld b, a
	ld a, [wPolicyWorkTick]
	cp b
	jr z, .idle
	ld a, [wPokedexAnimFlags]
	and $7c
	cp $04
	jr nz, .decode
	ld a, [wPokedexAnimStageTileCount]
	ld b, a
	ld a, [wPokedexAnimUploadOffset]
	cp b
	jr nc, .decode
	ld e, a
	ld d, 0
	ld hl, SOURCES
	add hl, de
	ld a, [wPokedexAnimDictionaryTilesRemaining]
	ld b, a
	ld a, [wPokedexAnimDictionaryTileCount]
	sub b
	cp [hl]
	jr c, .decode
	jr z, .decode
	ld a, $c0
	jr .record
.decode
	call Pokedex_AnimationDictionaryBelowTarget
	jr nc, .idle
	ld a, $40
.record
	ld c, a
	ldh a, [hVBlankCounter]
	ld [wPolicyWorkTick], a
	ld a, c
	ret
.idle
	xor a
	ret
Cost_ActionEnd::

Cost_PacingStart::
PolicyBeginLoop::
	ldh a, [hVBlankCounter]
	ld [wPolicyLoopTick], a
	ld hl, wPolicyControl
	res FINISH_USED, [hl]
	jp JoyTextDelay

PolicyEndLoop::
	ldh a, [hVBlank]
	bit 7, a
	jp z, DelayFrame
	ld hl, wPolicyControl
	bit AUDIO_DUE, [hl]
	jr z, .audio_done
	res AUDIO_DUE, [hl]
	call ServiceSampledCryAsync
.audio_done
	ldh a, [hVBlankCounter]
	ld b, a
	ld a, [wPolicyLoopTick]
	cp b
	jr nz, .returned_to_owner
	ld a, 1
	ld [wVBlankOccurred], a
.wait
	halt
	nop
	ld a, [wVBlankOccurred]
	and a
	jr nz, .wait
.returned_to_owner
	ld hl, wPolicyControl
	set AUDIO_DUE, [hl]
	ret
Cost_PacingEnd::

Cost_LifetimeStart::
PolicyAcquireQuietOwner::
; Caller: Selected reveal has already published empty OAM and the viewport.
; Fail closed if competing requests or unpublished viewport values remain.
	ldh a, [hVBlank]
	and 7
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
			ldh a, [$ff43]
		ELIF port == 1
			ldh a, [hSCY]
			ld b, a
			ldh a, [$ff42]
		ELIF port == 2
			ldh a, [hWY]
			ld b, a
			ldh a, [$ff4a]
		ELSE
			ldh a, [hWX]
			ld b, a
			ldh a, [$ff4b]
		ENDC
		cp b
		ret nz
	ENDR
	xor a
	ld [wPolicyControl], a
	ldh a, [hVBlankCounter]
	dec a
	ld [wPolicyWorkTick], a
	ld a, 1
	ldh [hOAMUpdate], a
	ld a, QUIET_OWNER
	ldh [hVBlank], a
	ret

PolicyReleaseQuietOwner::
	ldh a, [hVBlank]
	bit 7, a
	ret z
	and 7
	ldh [hVBlank], a
	xor a
	ldh [hOAMUpdate], a
	ld [wPolicyControl], a
	ret
Cost_LifetimeEnd::

Cost_FinishStart::
PolicyTryFinish::
; One optional complete remainder, never an unbounded catch-up loop.
	ldh a, [hVBlank]
	bit 7, a
	ret z
	ld hl, wPolicyControl
	bit FINISH_USED, [hl]
	ret nz
	ld a, [wPokedexAnimPlaybackState]
	cp 2
	ret nz
	ld a, [wPokedexAnimFlags]
	and $7c
	cp 4
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
	cp 21
	ret nc
	ld d, a
; Generated plans guarantee nondecreasing source IDs; check the final source.
	ld a, [wPokedexAnimStageTileCount]
	dec a
	ld e, a
	ld hl, SOURCES
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
	call PolicyAdmitFinish
	ret nc
	ld hl, wPolicyControl
	set FINISH_USED, [hl]
	call Pokedex_ServiceAnimationUploadChunk
	jp Pokedex_CommitDescriptionAnimation

PolicyAdmitFinish::
; d = complete ready remainder, 1..20. IME must be enabled by caller contract.
; These exact hardware checks intentionally reject unmodeled timer settings.
	ldh a, [$ff4d]
	bit 7, a
	jr nz, .reject
	ldh a, [hLCDCPointer]
	and a
	jr nz, .reject
	ldh a, [$ff40]
	bit 7, a
	jr z, .reject
	ldh a, [$ff07]
	and 7
	bit 2, a
	jr z, .timer_off
	cp 6
	jr z, .fast_timer
	cp 4
	jr nz, .reject
	ldh a, [$ff06]
	and a
	jr nz, .reject
	ldh a, [hSampledCryTimer]
	and a
	jr nz, .reject
	ld e, 20
	jr .time_gate
.fast_timer
	ldh a, [$ff06]
	cp 57
	jr nc, .reject
	ldh a, [hSampledCryTimer]
	and a
	ld e, 20
	jr z, .time_gate
	ldh a, [$ff06]
	cp 56
	jr nz, .reject
	call PolicyCheckAudioRunway
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
	ld hl, PolicyLatestLY
	add hl, de
	ld b, [hl]
	ldh a, [hVBlankCounter]
	inc a
	ld c, a
	ld a, [wPokedexAnimDeadline]
	sub c
	bit 7, a
	jr nz, .reject
	ldh a, [$ff41]
	and 3
	cp 1
	jr z, .reject
	ldh a, [$ff44]
	cp b
	ret
.reject
	and a
	ret

PolicyCheckAudioRunway::
; Return carry for enough cached blocks. Read shared counters with timer masked
; briefly, restore the caller's bank, then reopen interrupts before the LY gate.
	ld a, d
	dec a
	ld e, a
	push de
	ld d, 0
	ld hl, PolicyAudioMinimum
	add hl, de
	ld c, [hl]
	ldh a, [$ff70]
	push af
	ld a, 4
	ldh [$ff70], a
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
	ldh [$ff70], a
	pop de
	ei
	nop
	ld a, c
	rrca
	ret
Cost_FinishEnd::

Cost_TablesStart::
INCLUDE "finish_tables.inc"
Cost_TablesEnd::

; The following fragments are counted only; integration replaces their old
; counterparts. They are not entry points in a runnable cartridge.
Cost_HomeGuardStart::
	ldh a, [hVBlank]
	bit 7, a
	jr nz, .viewport_already_owned
.viewport_already_owned
Cost_HomeGuardEnd::

Cost_QueueGuardStart::
	ld a, [wPokedexAnimFlags]
	and $60
	ret nz
Cost_QueueGuardEnd::

Cost_QueueRouteStart::
	ldh a, [hVBlank]
	and QUIET_OWNER
	or 7
	ldh [hVBlank], a
Cost_QueueRouteEnd::

Cost_PublishRouteStart::
	ldh a, [hVBlank]
	and QUIET_OWNER
	ldh [hVBlank], a
Cost_PublishRouteEnd::

Cost_PublishGuardStart::
	ldh a, [$ff44]
	cp 144
	jp c, LinkedPublicationDefer
	ld b, a
	ldh a, [hVBlank]
	bit 7, a
	ld a, b
	jr z, .ordinary
	cp 149
	jr .check
.ordinary
	cp 146
.check
	jp nc, LinkedPublicationDefer
Cost_PublishGuardEnd::

Cost_ProducerArmStart::
	call PolicyChooseAction
	cp $40
	jr z, .decode
	cp $c0
	jr nz, .finished
	call Pokedex_ServiceAnimationUploadChunk
	jr .finished
.decode
	call Pokedex_ServiceAnimationDictionaryChunk
.finished
Cost_ProducerArmEnd::

Cost_OuterCallsStart::
	ld a, $a0
	ld hl, PolicyBeginLoop
	rst $08
	ld a, $a0
	ld hl, PolicyEndLoop
	rst $08
Cost_OuterCallsEnd::

Cost_HookCallsStart::
	call PolicyAcquireQuietOwner ; successful BeginDescription, before queue
	call PolicyReleaseQuietOwner ; CancelAnimationPrefetch, before state clear
	call PolicyReleaseQuietOwner ; ToggleDescription, before backing changes
	call PolicyTryFinish ; producer record_dictionary, before bookkeeping
Cost_HookCallsEnd::
