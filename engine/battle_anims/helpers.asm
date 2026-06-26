GetBattleAnimFrame:
.loop
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld a, [hl]
	and a
	jr z, .next_frame
	dec [hl]
	call .IsExtFrameset
	jr nc, .return_ext_frame
	call .GetPointer
	ld a, [hli]
	push af
	jr .okay

.next_frame
	call .IsExtFrameset
	jr nc, .next_ext_frame
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	inc [hl]
	call .GetPointer
	ld a, [hli]
	cp oamrestart_command
	jr z, .restart
	cp oamend_command
	jr z, .repeat_last

	push af
	ld a, [hl]
	push hl
	and ~(OAM_YFLIP << 1 | OAM_XFLIP << 1)
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], a
	pop hl
.okay
	ld a, [hl]
	and OAM_YFLIP << 1 | OAM_XFLIP << 1 ; The << 1 is compensated in the "oamframe" macro
	srl a
	ld [wBattleAnimTempFrameOAMFlags], a
	pop af
	ret

	.next_ext_frame
	call BattleAnimExt_LoadFrame

.return_ext_frame
	ld hl, BATTLEANIMSTRUCT_EXT_OAMFLAGS
	add hl, bc
	ld a, [hl]
	ld [wBattleAnimTempFrameOAMFlags], a
	ld hl, BATTLEANIMSTRUCT_EXT_OAMSET
	add hl, bc
	ld a, [hl]
	ret

.repeat_last
	xor a
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], a

	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	dec [hl]
	dec [hl]
	jr .loop

.restart
	xor a
	ld hl, BATTLEANIMSTRUCT_DURATION
	add hl, bc
	ld [hl], a

	dec a
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld [hl], a
	jr .loop

.GetPointer:
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld e, [hl]
	ld d, 0
	ld hl, BattleAnimFrameData
	add hl, de
	add hl, de
	ld e, [hl]
	inc hl
	ld d, [hl]
	ld hl, BATTLEANIMSTRUCT_FRAME
	add hl, bc
	ld l, [hl]
	ld h, 0
	add hl, hl
	add hl, de
	ret

.IsExtFrameset:
	ld hl, BATTLEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	inc hl          ; point to high byte (bank selector)
	ld a, [hl]
	cp 1            ; carry set = regular namespace, carry clear = extended namespace
	ret

GetBattleAnimOAMPointer:
	ld l, a
	ld h, 0
	ld de, BattleAnimOAMData
	add hl, hl
	add hl, hl
	add hl, de
	ret

LoadBattleAnimGFX:
	push hl
	push af
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	ld de, AnimObjGFX
	add hl, de
	ld c, [hl]
	inc hl
	ld b, [hl]
	inc hl
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop af
	cp BATTLE_ANIM_GFX_POKE_BALL
	call z, .GetBall
	pop de
	push bc
	call DecompressRequest2bpp
	pop bc
	ret

.GetBall:
	push bc
	ldh a, [rWBK]
	push af
	ld a, BANK(wCurItem)
	ldh [rWBK], a
	ld a, [wCurItem]
	ld b, a
	ld hl, BattleAnimBallData

.loop
	ld a, [hli]
	cp -1
	jr z, .got_ball
	cp b
	jr z, .got_ball
	ld de, BATTLE_ANIM_BALL_DATA_LENGTH - 1
	add hl, de
	jr .loop

.got_ball
	ld a, [hli]
	ldh [hTempBank], a
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, [hli]
	ld c, a
	ld b, [hl]
	push bc
	ld h, d
	ld l, e
	ld de, PAL_COLOR_SIZE
	add hl, de
	ld a, BANK(wOBPals2)
	ldh [rWBK], a
	ld de, wOBPals2 palette PAL_BATTLE_OB_RED color 1
	ld bc, PAL_COLOR_SIZE * 2
	ldh a, [hTempBank]
	call FarCopyBytes
	ld hl, WhitePalette
	ld de, wOBPals2 palette PAL_BATTLE_OB_GREEN color 1
	ld bc, PAL_COLOR_SIZE
	call CopyBytes
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	pop hl
	pop af
	ldh [rWBK], a
	pop bc
	ld b, BANK(AnimObjBattlePokeBallGFX)
	ret

INCLUDE "data/battle_anims/framesets.asm"

INCLUDE "data/battle_anims/oam.asm"

INCLUDE "data/battle_anims/object_gfx.asm"

INCLUDE "data/battle_anims/ball_colors.asm"
