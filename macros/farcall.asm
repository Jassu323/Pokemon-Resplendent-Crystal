; Far calls to another bank

MACRO farcall ; bank, address
	ld a, BANK(\1)
	ld hl, \1
	rst FarCall
ENDM

MACRO callfar ; address, bank
	ld hl, \1
	ld a, BANK(\1)
	rst FarCall
ENDM

MACRO homecall
	ldh a, [hROMBank]
	push af
	ld a, BANK(\1)
	rst Bankswitch
	call \1
	pop af
	rst Bankswitch
ENDM

; Discovery hooks preserve caller flags and pointers.
MACRO move_discovery_hook
	push af
	push hl
	farcall \1
	pop hl
	pop af
ENDM
