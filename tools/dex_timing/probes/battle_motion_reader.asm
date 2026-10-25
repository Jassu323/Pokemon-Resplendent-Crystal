; PRIVATE PROTOTYPE: two-byte motion samples, with independently completed work.
; DE = table (length byte, then pairs). BC = object. Carry = exhausted.
; No display waits, scheduler changes, or new WRAM state.
BattleMotion_ReadVar1:
	ld hl, BATTLEANIMSTRUCT_VAR1
	jr BattleMotion_Read

BattleMotion_ReadVar2:
	ld hl, BATTLEANIMSTRUCT_VAR2
BattleMotion_Read:
	add hl, bc
	ld a, [hl]
	inc [hl]
	ld h, d
	ld l, e
	cp [hl]
	jr nc, .done
	inc hl
	ld e, a
	ld d, 0
	sla e
	rl d
	add hl, de
	ld d, [hl]
	inc hl
	ld e, [hl]
	and a
	ret
.done
	scf
	ret
