; Generated Type-only audio copies. Do not edit.
; Shared decoder helpers and hardware writes remain unchanged.
PokedexTypes_AudioUpdate::
; called once per frame
	ldh a, [hSampledCryTimer]
	and a
	ret nz
	; no use updating audio if it's not playing
	ld a, [wMusicPlaying]
	and a
	ret z
	; start at ch1
	xor a
	ld [wCurChannel], a ; just
	ld [wSoundOutput], a ; off
	ld bc, wChannel1
.loop
	call PokedexTypes_AudioYield
	; is the channel active?
	ld hl, CHANNEL_FLAGS1
	add hl, bc
	bit SOUND_CHANNEL_ON, [hl]
	jp z, .nextchannel
	; check time left in the current note
	ld hl, CHANNEL_NOTE_DURATION
	add hl, bc
	ld a, [hl]
	cp 2 ; 1 or 0?
	jr c, .noteover
	dec [hl]
	jr .continue_sound_update

.noteover
	; reset vibrato delay
	ld hl, CHANNEL_VIBRATO_DELAY
	add hl, bc
	ld a, [hl]
	ld hl, CHANNEL_VIBRATO_DELAY_COUNT
	add hl, bc
	ld [hl], a
	; turn vibrato off for now
	ld hl, CHANNEL_FLAGS2
	add hl, bc
	res SOUND_PITCH_SLIDE, [hl]
	; get next note
	call PokedexTypes_AudioParse
.continue_sound_update
	call ApplyPitchSlide
	; duty cycle
	ld hl, CHANNEL_DUTY_CYCLE
	add hl, bc
	ld a, [hli]
	ld [wCurTrackDuty], a
	; volume envelope
	ld a, [hli]
	ld [wCurTrackVolumeEnvelope], a
	; frequency
	ld a, [hli]
	ld [wCurTrackFrequency], a
	ld a, [hl]
	ld [wCurTrackFrequency + 1], a
	; vibrato, noise
	call HandleTrackVibrato ; handle vibrato and other things
	call HandleNoise
	; turn off music when playing sfx?
	ld a, [wSFXPriority]
	and a
	jr z, .next
	; are we in a sfx channel right now?
	ld a, [wCurChannel]
	cp NUM_MUSIC_CHANS
	jr nc, .next
	; are any sfx channels active?
	; if so, mute
	ld hl, wChannel5Flags1
	bit SOUND_CHANNEL_ON, [hl]
	jr nz, .restnote
	ld hl, wChannel6Flags1
	bit SOUND_CHANNEL_ON, [hl]
	jr nz, .restnote
	ld hl, wChannel7Flags1
	bit SOUND_CHANNEL_ON, [hl]
	jr nz, .restnote
	ld hl, wChannel8Flags1
	bit SOUND_CHANNEL_ON, [hl]
	jr z, .next
.restnote
	ld hl, CHANNEL_NOTE_FLAGS
	add hl, bc
	set NOTE_REST, [hl] ; Rest
.next
	; are we in a sfx channel right now?
	ld a, [wCurChannel]
	cp NUM_MUSIC_CHANS
	jr nc, .sfx_channel
	ld hl, CHANNEL_STRUCT_LENGTH * NUM_MUSIC_CHANS + CHANNEL_FLAGS1
	add hl, bc
	bit SOUND_CHANNEL_ON, [hl]
	jr nz, .sound_channel_on
.sfx_channel
	call UpdateChannels
	ld hl, CHANNEL_TRACKS
	add hl, bc
	ld a, [wSoundOutput]
	or [hl]
	ld [wSoundOutput], a
.sound_channel_on
	; clear note flags
	ld hl, CHANNEL_NOTE_FLAGS
	add hl, bc
	xor a
	ld [hl], a
.nextchannel
	; next channel
	ld hl, CHANNEL_STRUCT_LENGTH
	add hl, bc
	ld c, l
	ld b, h
	ld a, [wCurChannel]
	inc a
	ld [wCurChannel], a
	cp NUM_CHANNELS ; are we done?
	jp nz, .loop ; do it all again

	call PlayDanger
	; fade music in/out
	call FadeMusic
	; write volume to hardware register
	ld a, [wVolume]
	ldh [rAUDVOL], a
	; write SO on/off to hardware register
	ld a, [wSoundOutput]
	ldh [rAUDTERM], a
	ret

PokedexTypes_AudioParse:
	call PokedexTypes_AudioYield
	call GetMusicByte
	cp sound_ret_cmd
	jr z, .sound_ret
	cp FIRST_MUSIC_CMD
	jp c, ParseMusic.readnote
.command
	call ParseMusicCommand
	jr PokedexTypes_AudioParse
.sound_ret
	ld hl, CHANNEL_FLAGS1
	add hl, bc
	bit SOUND_SUBROUTINE, [hl]
	jp z, ParseMusic.sound_ret
	jr .command

