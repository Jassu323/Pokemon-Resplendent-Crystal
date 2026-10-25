BattleIntroSlidingPics:
	ldh a, [rWBK]
	push af
	ld a, BANK(wLYOverrides)
	ldh [rWBK], a
	call .subfunction1
	ld a, LOW(rSCX)
	ldh [hLCDCPointer], a
	call .subfunction2
	xor a
	ldh [hLCDCPointer], a
	pop af
	ldh [rWBK], a
	ret

.subfunction1
	call .subfunction4
	ld a, $90
	ldh [hSCX], a
	ld a, %11100100
	call DmgToCgbBGPals
	lb de, %11100100, %11100100
	call DmgToCgbObjPals
	ret

.subfunction2
	push bc
	ld d, $90
	ld e, $72
	ld a, $48
	inc a
.loop1
	push af
	ldh a, [rVBK]
	ld b, a
	ld a, [wBattleFrontpicProducerState]
	and a
	jr z, .producer_serviced
	; Decode early enough for the next VBlank to upload without holding the slide.
	farcall BattleFrontpicProducer_Service
.producer_serviced
.loop2
	ldh a, [rLY]
	cp $60
	jr c, .loop2
	ld a, d
	ldh [hSCX], a
	call .subfunction5
	inc e
	inc e
	dec d
	dec d
	pop af
	push af
	cp $1
	jr z, .skip1
	push de
	call .subfunction3
	pop de

.skip1
	call .DelayFrame
	ld a, b
	ldh [rVBK], a
	pop af
	dec a
	jr nz, .loop1
	pop bc
	ret

.DelayFrame:
	call DelayFrame
	ld a, [wBattleFrontpicProducerState]
	and a
	ret z
	ldh a, [hDMATransfer]
	and a
	ret z
	ld a, [wBattleFrontpicProducerTransferBank]
	ldh [rVBK], a
	jr .DelayFrame

.subfunction3
	ld hl, wShadowOAMSprite00XCoord
	ld c, $12 ; 18
	ld de, OBJ_SIZE
.loop3
	dec [hl]
	dec [hl]
	add hl, de
	dec c
	jr nz, .loop3
	ret

.subfunction4
	ld hl, wLYOverrides
	ld a, $90
	ld bc, SCREEN_HEIGHT_PX
	call ByteFill
	ret

.subfunction5
	ld hl, wLYOverrides
	ld a, d
	ld c, $3e ; 62
.loop4
	ld [hli], a
	dec c
	jr nz, .loop4
	ld a, e
	ld c, $22 ; 34
.loop5
	ld [hli], a
	dec c
	jr nz, .loop5
	xor a
	ld c, $30 ; 48
.loop6
	ld [hli], a
	dec c
	jr nz, .loop6
	ret
