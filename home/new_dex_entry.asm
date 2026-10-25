SECTION "New Dex Entry Home", ROM0

ASSERT VBLANK_DEX_QUIET_F == 7

; Fixed-bank bridges only. Animation work and storage belong to registration.
NewDexEntry_VBlankDispatch::
; Entered by the existing quiet-owner viewport branch, not a call. Ordinary
; VBlank's 1bpp service cannot afford a new owner check before its LY cutoff.
	ldh a, [hVBlank]
	cp VBLANK_NEW_DEX_ENTRY
	jp nz, VBlank_Normal.viewport_owned
; Interrupts must not use FarCall's shared scratch.
	ldh a, [hROMBank]
	push af
	ld a, BANK(NewDexEntry_PublishAnimation)
	rst Bankswitch
	call NewDexEntry_PublishAnimation
	ld b, a
	pop af
	rst Bankswitch
	ld a, b
	and a
	jp nz, VBlank_Normal.done
	jp VBlank_Normal.viewport_owned

NewDexEntry_ServiceAfterDelayFrame::
	call ServiceSampledCryAsync
	push af ; preserve DelayFrame's zero result/flags, including outside this owner
	ldh a, [hVBlank]
	cp VBLANK_NEW_DEX_ENTRY
	jr nz, .return
; DelayFrames keeps its remaining frame count in c.
	push bc
	push de
	push hl
	ldh a, [hROMBank]
	push af
	ld a, BANK(NewDexEntry_ServiceAnimation)
	rst Bankswitch
	call NewDexEntry_ServiceAnimation
	pop af
	rst Bankswitch
	pop hl
	pop de
	pop bc
.return
	pop af
	ret

NewDexEntry_Get2bpp::
; Only the registration-local loader calls this bridge. Preserve its hl input.
	ld a, c
	cp 2
	jp c, Get2bpp
	ldh a, [hROMBank]
	push af
	ld a, BANK(NewDexEntry_UploadTiles)
	rst Bankswitch
	call NewDexEntry_UploadTiles
	pop af
	rst Bankswitch
	ret
