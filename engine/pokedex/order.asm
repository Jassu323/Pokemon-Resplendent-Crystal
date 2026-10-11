Pokedex_OrderMonsByMode:
	farcall PokedexPopover_OrderMons
	ret
Pokedex_ABCMode:
	ld a, [wCurDexMode]
	push af
	ld a, DEXMODE_ABC
	ld [wCurDexMode], a
	farcall PokedexPopover_OrderMons
	pop af
	ld [wCurDexMode], a
	ret
