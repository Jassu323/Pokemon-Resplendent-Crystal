; PRIVATE local motion samples. VAR1/VAR2 form an age word for this function.
; DE = word count, followed by signed XY offset pairs. Carry means exhausted.
BattleExpanded_Read16:
	push bc
	ld hl, BATTLEANIMSTRUCT_VAR1
	add hl, bc
	ld c, [hl]
	inc [hl]
	inc hl
	ld b, [hl]
	jr nz, .incremented
	inc [hl]
.incremented
	ld h, d
	ld l, e
	ld a, [hli]
	ld e, a
	ld d, [hl]
	inc hl
	ld a, b
	cp d
	jr c, .read
	jr nz, .done
	ld a, c
	cp e
	jr nc, .done
.read
	add hl, bc
	add hl, bc
	ld d, [hl]
	inc hl
	ld e, [hl]
	pop bc
	and a
	ret
.done
	pop bc
	scf
	ret
