Serial::
; The serial interrupt.

	push af
	push bc
	push de
	push hl

	ldh a, [hSerialConnectionStatus]
	inc a ; is it equal to CONNECTION_NOT_ESTABLISHED?
	jr z, .establish_connection

	ldh a, [rSB]
	ldh [hSerialReceive], a

	ldh a, [hSerialSend]
	ldh [rSB], a

	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	jr z, .player2

	ld a, SC_EXTERNAL
	ldh [rSC], a
	ld a, SC_START | SC_EXTERNAL
	ldh [rSC], a
	jr .player2

.establish_connection
	ldh a, [rSB]
	cp USING_EXTERNAL_CLOCK
	jr z, .player1
	cp USING_INTERNAL_CLOCK
	jr nz, .player2

.player1
	ldh [hSerialReceive], a
	ldh [hSerialConnectionStatus], a
	cp USING_INTERNAL_CLOCK
	jr z, ._player2

	xor a
	ldh [rSB], a

	ld a, 3
	ldh [rDIV], a
.delay_loop
	ldh a, [rDIV]
	bit 7, a ; wait until rDIV has incremented from 3 to $80 or more
	jr nz, .delay_loop

	ld a, SC_EXTERNAL
	ldh [rSC], a
	ld a, SC_START | SC_EXTERNAL
	ldh [rSC], a
	jr .player2

._player2
	xor a
	ldh [rSB], a

.player2
	ld a, TRUE
	ldh [hSerialReceivedNewData], a
	ld a, SERIAL_NO_DATA_BYTE
	ldh [hSerialSend], a

.end
	pop hl
	pop de
	pop bc
	pop af
	reti

; Link-cable exchange helpers were relocated to bank $5B for the Sampled Cry
; Audio Playback System in the NewAdditions/Pokémon branch. If link-cable
; functionality breaks, start by checking engine/link/serial_exchange.asm.

LinkTransfer::
	push bc
	ld b, SERIAL_TIMECAPSULE
	ld a, [wLinkMode]
	cp LINK_TIMECAPSULE
	jr z, .got_high_nybble
	ld b, SERIAL_TIMECAPSULE
	jr c, .got_high_nybble
	cp LINK_TRADECENTER
	ld b, SERIAL_TRADECENTER
	jr z, .got_high_nybble
	ld b, SERIAL_BATTLE

.got_high_nybble
	call .Receive
	ld a, [wPlayerLinkAction]
	add b
	ldh [hSerialSend], a
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	jr nz, .player_1
	ld a, SC_INTERNAL
	ldh [rSC], a
	ld a, SC_START | SC_INTERNAL
	ldh [rSC], a

.player_1
	call .Receive
	pop bc
	ret

.Receive:
	ldh a, [hSerialReceive]
	ld [wOtherPlayerLinkMode], a
	and $f0
	cp b
	ret nz
	xor a
	ldh [hSerialReceive], a
	ld a, [wOtherPlayerLinkMode]
	and $f
	ld [wOtherPlayerLinkAction], a
	ret

LinkDataReceived::
; Let the other system know that the data has been received.
	xor a
	ldh [hSerialSend], a
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	ret nz
	ld a, SC_INTERNAL
	ldh [rSC], a
	ld a, SC_START | SC_INTERNAL
	ldh [rSC], a
	ret
