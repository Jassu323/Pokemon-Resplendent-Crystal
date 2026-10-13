SECTION "Lifecycle Late Mask Probe", ROMX[PROBE_PC], BANK[PROBE_BANK]
ProbeLateMask:
	call CLEAR_SPRITES
	jp CLEAR_PALETTES
ProbeLateMaskEnd:
