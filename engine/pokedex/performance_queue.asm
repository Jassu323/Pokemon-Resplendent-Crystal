; Finish the current Info job and coalesce newer requests.
PokedexPerf_QueueInfo:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld a, [wPokedexSelectedView]
	cp DEXSELECT_VIEW_INFO
	jr nz, .idle
	ld a, [wPokedexInfoPendingPage]
	and a
	jr nz, .busy
	ld a, [wPokedexInfoState]
	and a
	jr nz, .busy
	ld a, [wPokedexOwnerTransition]
	cp POKEDEX_OWNER_TRANSITION_INFO
	jr nz, .idle
.busy
	ld a, [wPokedexInfoPendingPage]
	and a
	jr nz, .pending
	ld a, [wPokedexInfoPage]
	inc a
.pending
	ld hl, wPokedexInfoPageCount
	cp [hl]
	jr c, .save
	xor a
.save
	inc a
	ld [wPokedexInfoPendingPage], a
	pop af
	ldh [rSVBK], a
	scf
	ret
.idle
	pop af
	ldh [rSVBK], a
	and a
	ret

PokedexPerf_BeginPendingInfo:
; Called in bank 3, after the preceding VBlank commit has completed.
	ld a, [wPokedexInfoState]
	and a
	ret nz
	ld a, [wPokedexOwnerTransition]
	and a
	ret nz
	ld a, [wPokedexInfoPendingPage]
	and a
	ret z
	dec a
	ld [wPokedexInfoPage], a
	xor a
	ld [wPokedexInfoPendingPage], a
	ld a, POKEDEX_INFO_INITIALIZE
	ld [wPokedexInfoState], a
	ret
