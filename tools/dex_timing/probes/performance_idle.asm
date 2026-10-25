; PRIVATE PERFORMANCE PROTOTYPE. Only used when portrait and cries are idle.
PokedexPerf_CanBatch:
	ld a, [wPokedexAnimPlaybackState]
	cp POKEDEX_ANIM_PLAYBACK_PLAYING
	jr z, .no
	ldh a, [hSampledCryTimer]
	and a
	jr nz, .no
	ld a, [wChannel5Flags1]
	ld b, a
	ld a, [wChannel6Flags1]
	or b
	ld b, a
	ld a, [wChannel7Flags1]
	or b
	ld b, a
	ld a, [wChannel8Flags1]
	or b
	and 1 << SOUND_CHANNEL_ON
	jr nz, .no
	scf
	ret
.no
	and a
	ret

PokedexPerf_IdleUpload:
; HL=bank-3 source, DE=inactive atlas, C<=8. No sampled IRQ is active.
.wait
	ldh a, [rLY]
	cp 144
	jr c, .wait
	cp 151
	jr nc, .wait
	di
	ld a, h
	ldh [rVDMA_SRC_HIGH], a
	ld a, l
	and $f0
	ldh [rVDMA_SRC_LOW], a
	ld a, d
	and $1f
	ldh [rVDMA_DEST_HIGH], a
	ld a, e
	and $f0
	ldh [rVDMA_DEST_LOW], a
	ld a, c
	dec a
	ldh [rVDMA_LEN], a
	ei
	ret
