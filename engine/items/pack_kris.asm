DrawKrisPackGFX:
	ld hl, PackFGFXPointers
	add hl, de
	add hl, de
	ld a, [hli]
	ld e, a
	ld d, [hl]
	ld hl, vTiles2 tile PACK_GFX_TILE
	lb bc, BANK(PackFGFX), 15
	call Request2bpp
	ret

PackFGFXPointers:
	dw PackFGFX + (15 tiles) * 1 ; ITEM_POCKET
	dw PackFGFX + (15 tiles) * 3 ; BALL_POCKET
	dw PackFGFX + (15 tiles) * 0 ; KEY_ITEM_POCKET
	dw PackFGFX + (15 tiles) * 2 ; BERRY_POCKET
	dw PackFGFX + (15 tiles) * 4 ; MEDICINE_POCKET

SECTION "Kris Pack Graphics", ROMX

PackFGFX:
INCBIN "gfx/pack/pack_f.2bpp"
