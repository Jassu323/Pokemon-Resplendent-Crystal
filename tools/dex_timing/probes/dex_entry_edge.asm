SECTION "Lifecycle Entry Edge Probe", ROMX[PROBE_PC], BANK[PROBE_BANK]
ProbeEntryEdge:
	ldh a, [H_CGB]
	and a
	jr z, .compat
	call COPY_EDGE
	ldh a, [$ff4f]
	push af
	xor a
	ldh [$ff4f], a
	ld hl, $9914
	ld [hl], $67
	pop af
	ldh [$ff4f], a
	jp ENABLE_LCD
.compat
	call ENABLE_LCD
	ld a, OLD_EDGE_BANK
	ld hl, OLD_EDGE
	rst FAR_CALL
	ret
ProbeEntryEdgeEnd:
