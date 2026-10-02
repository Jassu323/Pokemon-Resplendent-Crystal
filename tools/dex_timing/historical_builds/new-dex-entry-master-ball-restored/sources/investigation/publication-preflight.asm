; HOST-ONLY diagnostic prototype. Never included in the game build.
; Fixed destination $9821, seven rows, seven columns, no low-byte wrap
; inside a row. Callers do not consume the resulting HL/DE/BC values.
SECTION "Private New Entry Publication Preflight", ROMX[$7906], BANK[$a5]

PrivateCopyMap:
	FOR row, 7
		REPT 6
			ld a, [hli]
			ld [de], a
			inc e
		ENDR
		ld a, [hli]
		ld [de], a
		IF row < 6
			ld e, LOW($9821 + (row + 1) * 32)
		ENDC
	ENDR
	ret
PrivateCopyMapEnd:

PrivateFillAttrs:
	ld h, d
	ld l, e
	FOR row, 7
		REPT 7
			ld [hli], a
		ENDR
		IF row < 6
			ld l, LOW($9821 + (row + 1) * 32)
		ENDC
	ENDR
	ret
PrivateFillAttrsEnd:
