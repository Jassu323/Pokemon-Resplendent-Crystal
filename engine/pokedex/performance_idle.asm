; Dex performance helpers. Only used when portrait and cries are idle.
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

