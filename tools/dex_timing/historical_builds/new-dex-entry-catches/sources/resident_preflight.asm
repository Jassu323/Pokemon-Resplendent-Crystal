; HOST-ONLY EXECUTABLE PREFLIGHT. Never included by the game build.
; State aliases reuse the legacy animation owner, not padding or Dex WRAM0.
INCLUDE "preflight_linked.inc"

DEF OWNER EQU $88
DEF Flags EQU wPokeAnimSceneIndex
DEF Timeline EQU wPokeAnimPointer
DEF BaseCount EQU wPokeAnimGraphicStartTile
DEF Deadline EQU wPokeAnimWaitCounter
DEF Duration EQU wPokeAnimParameter
DEF FrameID EQU wPokeAnimCommand
DEF Publications EQU wPokeAnimFrame
DEF Misses EQU wPokeAnimJumptableIndex
DEF SavedVBlank EQU wPokeAnimRepeatTimer
DEF SavedOAM EQU wPokeAnimCurBitmask
DEF Map EQU wPokeAnimFrameTiles
DEF Pairs EQU wTempTilemap
DEF ACTIVE EQU 0
DEF READY EQU 1
DEF FINISH EQU 2
DEF FIRST EQU 3
DEF ACK EQU 4

SECTION "Preflight Home", ROM0[$3dc0]
ProtoHomeStart::
ProtoHomeStep::
	ldh a, [hROMBank]
	push af
	ld a, BANK(ProtoStep)
	rst $10
	call ProtoStep
	pop af
	rst $10
	ret

ProtoHomeVBlank::
	ldh a, [hVBlank]
	cp OWNER
	jp nz, UpdateBGMapBuffer
	ldh a, [hROMBank]
	push af
	ld a, BANK(ProtoPublish)
	rst $10
	call ProtoPublish
	ld b, a
	pop af
	rst $10
	ld a, b
	and a
	ret z
	scf
	ret

ProtoHomeDelayTail::
	call ServiceSampledCryAsync
	ldh a, [hVBlank]
	cp OWNER
	ret nz
	push bc
	push de
	push hl
	ldh a, [hROMBank]
	push af
	ld a, BANK(ProtoService)
	rst $10
	call ProtoService
	pop af
	rst $10
	pop hl
	pop de
	pop bc
	ret

ProtoHomeCancel::
	ldh a, [hROMBank]
	push af
	ld a, BANK(ProtoCancel)
	rst $10
	call ProtoCancel
	pop af
	rst $10
	ret

ProtoHomeUpload::
	ld a, c
	cp 2
	jp c, Get2bpp
	ldh a, [hROMBank]
	push af
	ld a, BANK(ProtoUpload)
	rst $10
	call ProtoUpload
	pop af
	rst $10
	ret
ProtoHomeEnd::

SECTION "Preflight Resident Owner", ROMX[$4000], BANK[$a6]
ProtoStart::
ProtoStep::
	ldh a, [$ff70]
	push af
	ld a, 2
	ldh [$ff70], a
	ld a, [Flags]
	and a
	call z, ProtoInitialize
	pop af
	ldh [$ff70], a
	jp DelayFrame

ProtoInitialize::
	ld de, wTilemap + 21
	ld a, BANK_PokeAnim_InitDexFrameProducer
	ld hl, PokeAnim_InitDexFrameProducer
	rst $08
	ld a, e
	ld [Timeline], a
	ld a, d
	ld [Timeline + 1], a
	ld b, c
	xor a
.square
	add c
	dec b
	jr nz, .square
	ld [BaseCount], a
	ldh a, [hVBlank]
	ld [SavedVBlank], a
	ldh a, [hOAMUpdate]
	ld [SavedOAM], a
	ld a, 1 << ACTIVE | 1 << FIRST
	ld [Flags], a
	call ProtoBuild
	ld a, [wPokeAnimSpecies]
	call PlayMonCry2
	ldh a, [hVBlankCounter]
	inc a
	ld [Deadline], a
	xor a
	ldh [hBGMapMode], a
	ld a, 1
	ldh [hOAMUpdate], a
	ld a, OWNER
	ldh [hVBlank], a
	ret

ProtoService::
	ldh a, [$ff70]
	push af
	ld a, 2
	ldh [$ff70], a
	ld hl, Flags
	bit ACK, [hl]
	jr z, .build
	res ACK, [hl]
	ld hl, Map
	ld de, wTilemap + 21
	call ProtoCopyBacking
	ld a, [Flags]
	and 1 << FIRST | 1 << FINISH
	jr z, .backed
	ld a, 9
	ld hl, Flags
	bit FINISH, [hl]
	jr z, .attr
	ld a, 1
.attr
	res FIRST, [hl]
	ld de, wAttrmap + 21
	call ProtoFillBacking
.backed
	ld hl, Flags
	bit FINISH, [hl]
	jr nz, .complete
	ld a, [Duration]
	ld hl, Deadline
	add [hl]
	ld [hl], a
.build
	ld a, [Flags]
	bit READY, a
	jr nz, .return
	bit ACTIVE, a
	call nz, ProtoBuild
.return
	pop af
	ldh [$ff70], a
	ret
.complete
	call ProtoRestore
ProtoCompleted::
	jr ProtoService.return

ProtoReadEvent::
	ld a, [Timeline]
	ld l, a
	ld a, [Timeline + 1]
	ld h, a
.read
	ld a, $a5
	call GetFarByte
	inc hl
	cp $f0
	jr z, .finish
	cp $f1
	jr z, .loop
	ld b, a
	and $f
	jr nz, .duration
	ld a, $a5
	call GetFarByte
	inc hl
.duration
	ld [Duration], a
	ld a, b
	swap a
	and $f
	ld [FrameID], a
	inc hl ; resident dictionary makes the high-water byte unnecessary here
.save
	ld a, l
	ld [Timeline], a
	ld a, h
	ld [Timeline + 1], a
	ret
.finish
	xor a
	ld [FrameID], a
	ld [Duration], a
	ld a, [Flags]
	or 1 << FINISH
	ld [Flags], a
	jr .save
.loop
	push hl
	ld a, $a5
	call GetFarWord
	ld d, h
	ld e, l
	pop hl
	inc hl
	inc hl
	ld a, l
	sub e
	ld l, a
	ld a, h
	sbc d
	ld h, a
	jr .read

ProtoBuild::
	call ProtoReadEvent
	ld hl, ProtoBase
	ld de, Map
	ld bc, 49
	call CopyBytes
	ld a, [FrameID]
	and a
	jr z, .ready
	ld b, a
	ld a, BANK_PokeAnim_GetDexFramePlanPointer
	ld hl, PokeAnim_GetDexFramePlanPointer
	rst $08
	ld a, d
	call GetFarByte
	push af
	inc hl
	inc hl
	add a
	ld c, a
	ld b, 0
	ld a, d
	ld de, Pairs
	call FarCopyBytes
	pop af
	ld b, a
	and a
	jr z, .ready
	ld hl, Pairs
.pair
	ld a, [hli]
	ld c, a
	and $7f
	add LOW(Map)
	ld e, a
	ld a, HIGH(Map)
	adc 0
	ld d, a
	ld a, [hli]
	bit 7, c
	jr nz, .store
	ld c, a
	ld a, [BaseCount]
	cpl
	inc a
	add c
	add 49
	cp 127
	jr c, .store
	inc a ; resident loader leaves tile $7f blank
.store
	ld [de], a
	dec b
	jr nz, .pair
.ready
ProtoPrepared::
	ld hl, Flags
	set READY, [hl]
	ret

ProtoPublish::
	ldh a, [$ff44]
	cp 144
	jr c, .skip
	cp 153
	jr c, .vblank
.skip
	xor a
	ret
.vblank
	ldh a, [$ff70]
	push af
	ldh a, [$ff4f]
	push af
	ld a, 2
	ldh [$ff70], a
	xor a
	ldh [$ff4f], a
	ld a, [wTilemap + 17 * 20 + 18]
	ld [$9800 + 17 * 32 + 18], a
	ld a, [Flags]
	and 1 << ACTIVE | 1 << READY
	cp 1 << ACTIVE | 1 << READY
	jr nz, ProtoNoPublish
	ldh a, [hVBlankCounter]
	ld b, a
	ld a, [Deadline]
	sub b
	jr z, .due
	bit 7, a
	jr z, ProtoNoPublish
	ld hl, Misses
	inc [hl]
.due
	ld b, 149
	ld a, [Flags]
	and 1 << FIRST | 1 << FINISH
	jr z, .cutoff
	ld b, 146
.cutoff
	ldh a, [$ff44]
	cp b
	jr nc, ProtoNoPublish
	ld hl, Map
	ld de, $9821
	call ProtoCopyVRAM
	ld a, [Flags]
	and 1 << FIRST | 1 << FINISH
	jr z, .published
	ld a, 1
	ldh [$ff4f], a
	ld a, [Flags]
	bit FINISH, a
	ld a, 9
	jr z, .attr
	ld a, 1
.attr
	ld de, $9821
	call ProtoFillVRAM
.published
	ld hl, Publications
	inc [hl]
	ld hl, Flags
	res READY, [hl]
	set ACK, [hl]
ProtoPublished::
	pop af
	ldh [$ff4f], a
	pop af
	ldh [$ff70], a
	ld a, 1
	ret
ProtoNoPublish::
	pop af
	ldh [$ff4f], a
	pop af
	ldh [$ff70], a
	xor a
	ret

MACRO copy_rows
	ld b, 7
.row\@
	REPT 7
		ld a, [hli]
		ld [de], a
		inc de
	ENDR
	ld a, e
	add \1 - 7
	ld e, a
	jr nc, .carry\@
	inc d
.carry\@
	dec b
	jr nz, .row\@
	ret
ENDM
ProtoCopyBacking::
	copy_rows 20
ProtoCopyVRAM::
	copy_rows 32

MACRO fill_rows
	ld c, a
	ld b, 7
.row\@
	ld a, c
	REPT 7
		ld [de], a
		inc de
	ENDR
	ld a, e
	add \1 - 7
	ld e, a
	jr nc, .carry\@
	inc d
.carry\@
	dec b
	jr nz, .row\@
	ret
ENDM
ProtoFillBacking::
	fill_rows 20
ProtoFillVRAM::
	fill_rows 32

ProtoRestore::
	ld a, [SavedVBlank]
	ldh [hVBlank], a
	ld a, [SavedOAM]
	ldh [hOAMUpdate], a
	xor a
	ld [Flags], a
	ld [wFrameCounter], a
	ret
ProtoCancel::
	xor a
	ld [wFrameCounter], a
	ldh a, [hVBlank]
	cp OWNER
	ret nz
	ldh a, [$ff70]
	push af
	ld a, 2
	ldh [$ff70], a
	call ProtoRestore
	pop af
	ldh [$ff70], a
	ret

ProtoBase:
	FOR y, 7
		FOR x, 7
			db x * 7 + y
		ENDR
	ENDR
ProtoOwnerEnd::

; Separate startup experiment. Source is already resident SRAM/WRAM.
; Queue at most 32 tiles per VBlank, keeping normal sound/joypad servicing.
; The padded SRAM base begins at $a001; stage its chunks in the unused upper
; part of the same SRAM scratch union so DMA never rounds the source down.
ProtoUpload::
ASSERT sScratch + $320 >= sPaddedEnemyFrontPic + 49 * 16
ASSERT $320 + 32 * 16 <= $60 * 16
.next
	ld a, c
	cp 2
	jp c, Get2bpp
	cp 32
	jr c, .chunk
	ld a, 32
.chunk
	ld b, a
	push bc
	push de
	push hl
	ld a, e
	and $f
	jr z, .aligned
	push bc
	push hl
	ld h, d
	ld l, e
	ld de, sScratch + $320
	ld c, b
	ld b, 0
	REPT 4
		sla c
		rl b
	ENDR
	call CopyBytes
	ld de, sScratch + $320
	pop hl
	pop bc
.aligned
	ld a, d
	ldh [$ff51], a
	ld a, e
	ldh [$ff52], a
	ld a, h
	and $1f
	ldh [$ff53], a
	ld a, l
	ldh [$ff54], a
	ld a, b
	dec a
	ldh [hDMATransfer], a
	ld a, BANK_WaitDMATransfer
	ld hl, WaitDMATransfer
	rst $08
	pop hl
	pop de
	pop bc
	ld a, c
	sub b
	push af
	ld c, b
	ld b, 0
	REPT 4
		sla c
		rl b
	ENDR
	add hl, bc
	ld a, e
	add c
	ld e, a
	ld a, d
	adc b
	ld d, a
	pop af
	ld c, a
	and a
	jr nz, .next
	ret
ProtoEnd::
