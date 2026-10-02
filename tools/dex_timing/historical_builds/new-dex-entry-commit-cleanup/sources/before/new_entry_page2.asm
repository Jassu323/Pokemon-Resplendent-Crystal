; HOST-ONLY EXPERIMENT. Assembled into verified free ROMX in a private ROM.
; No runtime source files include this file.
INCLUDE "page2-bindings.asm"

SECTION "New Entry Page Two Experiment", ROMX[$7800], BANK[$77]
NewDexEntry_DisplayPage2::
	IF EXPERIMENT_AUDIO_POINTS == 3
	call NewDexEntry_ServiceAfterDelayFrame
	ELSE
		IF EXPERIMENT_AUDIO_POINTS == 1
		call ServiceSampledCryAsync
		ENDC
	call NewDexEntry_PageService
	ENDC
	xor a
	ldh [hBGMapMode], a
	ld a, [wTempSpecies]
	ld b, a
	ld a, B_GetDexEntryPointer
	ld hl, GetDexEntryPointer
	rst FarCall
	ld h, d
	ld l, e
; Skip the category, dimensions, and first-page bytes without rendering them.
.category
	ld a, b
	call GetFarByte
	inc hl
	cp $50
	jr nz, .category
	inc hl
	inc hl
	inc hl
	inc hl
.page1
	ld a, b
	call GetFarByte
	inc hl
	cp $50
	jr nz, .page1
	IF EXPERIMENT_AUDIO_POINTS == 3
	call NewDexEntry_ServiceAfterDelayFrame
	ELSE
	call NewDexEntry_PageService
	ENDC
	push bc
	push hl
	ld bc, $0512
	ld hl, wTilemap + 10 * 20 + 2
	call ClearBox
	ld a, $58
	ld [wTilemap + 9 * 20 + 2], a
	pop de
	pop bc
	ld a, b
	ld hl, wTilemap + 10 * 20 + 2
	call PlaceFarString
	IF EXPERIMENT_AUDIO_POINTS == 3
	call NewDexEntry_ServiceAfterDelayFrame
	ELSE
	call NewDexEntry_PageService
	ENDC
	ret
	IF EXPERIMENT_AUDIO_POINTS != 3
NewDexEntry_PageService::
; Map acknowledgement/preparation is bounded. Audio retains its normal
; DelayFrame refill opportunities instead of adding a batch at every point.
	push af
	ldh a, [hVBlank]
	cp $88
	jr nz, .done
	push bc
	push de
	push hl
	ld a, B_NewDexEntry_ServiceAnimation
	ld hl, NewDexEntry_ServiceAnimation
	rst FarCall
	pop hl
	pop de
	pop bc
.done
	pop af
	ret
	ENDC
NewDexEntry_PageExperimentEnd::

	IF EXPERIMENT_ACK_GUARD
SECTION "New Entry ACK Guard Experiment", ROMX[$7f00], BANK[B_NewDexEntry_ServiceAnimation]
NewDexEntry_PageACKGuard::
; The original two independent flag reads can straddle publication. Use the
; fresh snapshot for ACK as well as READY before overwriting the shared map.
	ld a, [wNewDexEntryAnimFlags]
	bit 4, a
	jp nz, OriginalServiceAck
	jp OriginalServiceBuild + 3
NewDexEntry_PageACKGuardEnd::
	ENDC
