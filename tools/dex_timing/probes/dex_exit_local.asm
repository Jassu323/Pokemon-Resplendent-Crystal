SECTION "Lifecycle Exit Local Probe", ROMX[PROBE_PC], BANK[PROBE_BANK]
ProbeExitLocal:
	ldh a, [H_CGB]
	and a
	jp z, CLOSE_SUBMENU
	call CLEAR_PALETTES
	call RELOAD_TILES
	call UPDATE_SPRITES
	call EXIT_MENU
	ld b, MAP_PALS
	call GET_LAYOUT
	ld a, OW_PAL_BANK
	ld hl, OW_PAL
	rst FAR_CALL
IF DEF(PAL_GUARD)
	; The existing map copier can release a pending VBlank IRQ on line 127.
	; Keep palette uploads queued until a fresh physical VBlank has passed.
	ldh a, [H_PAL_UPDATE]
	push af
	xor a
	ldh [H_PAL_UPDATE], a
ENDC
	call COPY_MAP
IF DEF(PAL_GUARD)
	call DELAY_FRAME
	pop af
	ldh [H_PAL_UPDATE], a
ENDC
	ld a, 1
	ldh [H_BG_MODE], a
	ld a, FADE_BANK
	ld hl, FADE_IN
	rst FAR_CALL
	jp ENABLE_SPRITES
ProbeExitLocalEnd:
