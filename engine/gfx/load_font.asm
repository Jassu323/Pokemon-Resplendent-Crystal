INCLUDE "gfx/font.asm"

EnableHDMAForGraphics:
	db FALSE

Get1bppOptionalHDMA: ; unreferenced
	ld a, [EnableHDMAForGraphics]
	and a
	jp nz, Get1bppViaHDMA
	jp Get1bpp

Get2bppOptionalHDMA: ; unreferenced
	ld a, [EnableHDMAForGraphics]
	and a
	jp nz, Get2bppViaHDMA
	jp Get2bpp

_LoadStandardFont::
	ld de, Font
	ld hl, vTiles1
	lb bc, BANK(Font), 128 ; 'A' to '9'
	ldh a, [rLCDC]
	bit B_LCDC_ENABLE, a
	jp z, Copy1bpp

	ld de, Font
	ld hl, vTiles1
	lb bc, BANK(Font), 32 ; 'A' to ']'
	call Get1bppViaHDMA
	ld de, Font + 32 * TILE_1BPP_SIZE
	ld hl, vTiles1 tile $20
	lb bc, BANK(Font), 32 ; 'a' to $bf
	call Get1bppViaHDMA
	ld de, Font + 64 * TILE_1BPP_SIZE
	ld hl, vTiles1 tile $40
	lb bc, BANK(Font), 32 ; 'Ä' to '←'
	call Get1bppViaHDMA
	ld de, Font + 96 * TILE_1BPP_SIZE
	ld hl, vTiles1 tile $60
	lb bc, BANK(Font), 32 ; '\'' to '9'
	call Get1bppViaHDMA
	ret

_LoadFontsExtra1::
	ld de, FontsExtra_SolidBlackGFX
	ld hl, vTiles2 tile '■' ; $60
	lb bc, BANK(FontsExtra_SolidBlackGFX), 1
	call Get1bppViaHDMA
	ld de, PokegearPhoneIconGFX
	ld hl, vTiles2 tile '☎' ; $62
	lb bc, BANK(PokegearPhoneIconGFX), 1
	call Get2bppViaHDMA
	ld de, FontExtra + 3 tiles ; '<BOLD_D>'
	ld hl, vTiles2 tile '<BOLD_D>'
	lb bc, BANK(FontExtra), 22 ; '<BOLD_D>' to 'ぉ'
	call Get2bppViaHDMA
	jr LoadFrame

_LoadFontsExtra2::
	ld de, FontsExtra2_UpArrowGFX
	ld hl, vTiles2 tile '▲' ; $61
	ld b, BANK(FontsExtra2_UpArrowGFX)
	ld c, 1
	call Get2bppViaHDMA
	ret

_LoadFontsBattleExtra::
	ld de, FontBattleExtra
	ld hl, vTiles2 tile $60
	lb bc, BANK(FontBattleExtra), 25
	call Get2bppViaHDMA
	jr LoadFrame

LoadFrame:
	ld a, [wTextboxFrame]
	maskbits NUM_FRAMES
	ld bc, TEXTBOX_FRAME_TILES * TILE_1BPP_SIZE
	ld hl, Frames
	call AddNTimes
	ld d, h
	ld e, l
	ld hl, vTiles2 tile '┌' ; $79
	lb bc, BANK(Frames), TEXTBOX_FRAME_TILES ; '┌' to '┘'
	call Get1bppViaHDMA
	ld hl, vTiles2 tile ' ' ; $7f
	ld de, TextboxSpaceGFX
	lb bc, BANK(TextboxSpaceGFX), 1
	call Get1bppViaHDMA
	ret

LoadBattleFontsHPBar:
	call LoadBattleHUDBarFontTiles
	call LoadFrame
	jr LoadHPBar_NoFont

LoadHPBar:
	call LoadBattleHUDBarFontTiles

LoadHPBar_NoFont:
	ld de, ExpBarGFX
	ld hl, vTiles2 tile BATTLE_HUD_EXP_PARTIAL_TILE
	lb bc, BANK(ExpBarGFX), 7
	call Get2bppViaHDMA
	ld de, ExpBarGFX + 7 tiles
	ld hl, vTiles1 tile BATTLE_HUD_PARTY_ICON_DEST_TILE
	lb bc, BANK(ExpBarGFX), 2
	call Get2bppViaHDMA

	ld de, EnemyHPBarBorderGFX
	ld hl, vTiles2 tile BATTLE_HUD_PLAYER_HP_END_TILE
	lb bc, BANK(EnemyHPBarBorderGFX), 2
	call Get1bppViaHDMA
	ld de, EnemyHPBarBorderGFX + 3 * TILE_1BPP_SIZE
	ld hl, vTiles2 tile BATTLE_HUD_PLAYER_BOTTOM_LEFT_TILE
	lb bc, BANK(EnemyHPBarBorderGFX), 1
	call Get1bppViaHDMA
	ld de, HPExpBarBorderGFX
	ld hl, vTiles2 tile BATTLE_HUD_PLAYER_RIGHT_TILE
	lb bc, BANK(HPExpBarBorderGFX), 2
	call Get1bppViaHDMA
	ld de, HPExpBarBorderGFX + 3 * TILE_1BPP_SIZE
	ld hl, vTiles2 tile BATTLE_HUD_BOTTOM_TILE
	lb bc, BANK(HPExpBarBorderGFX), 3
	call Get1bppViaHDMA
	ret

LoadBattleHUDBarFontTiles:
	ld de, FontBattleExtra
	ld hl, vTiles2 tile BATTLE_HUD_HP_LABEL_TILE
	lb bc, BANK(FontBattleExtra), 2 ; HP label
	call Get2bppViaHDMA
	ld de, FontBattleExtra + 2 tiles
	ld hl, vTiles2 tile BATTLE_HUD_BAR_EMPTY_TILE
	lb bc, BANK(FontBattleExtra), 8 ; empty bar + 1px-7px HP bar fills
	call Get2bppViaHDMA
	ld de, FontBattleExtra + 10 tiles
	ld hl, vTiles2 tile BATTLE_HUD_BAR_FULL_TILE
	lb bc, BANK(FontBattleExtra), 2 ; full bar + enemy HP end cap
	call Get2bppViaHDMA
	ld de, FontBattleExtra + 14 tiles ; '<LV>'
	ld hl, vTiles2 tile BATTLE_HUD_LEVEL_TILE
	lb bc, BANK(FontBattleExtra), 1
	call Get2bppViaHDMA
	ld de, FontBattleExtra + 15 tiles
	ld hl, vTiles2 tile BATTLE_HUD_EXP_TAIL_RIGHT_TILE
	lb bc, BANK(FontBattleExtra), 1
	call Get2bppViaHDMA
	ld de, FontBattleExtra + 31 tiles
	ld hl, vTiles2 tile BATTLE_HUD_EXP_TAIL_LEFT_TILE
	lb bc, BANK(FontBattleExtra), 1
	call Get2bppViaHDMA
	ret

StatsScreen_LoadFont:
	call LoadHPBar
	call LoadStatsScreenLegacyFontTiles
LoadStatsScreenPageTilesGFX:
	ld de, StatsScreenPageTilesGFX
	ld hl, vTiles2 tile $31
	lb bc, BANK(StatsScreenPageTilesGFX), 26
	call Get2bppViaHDMA
	ret

LoadStatsScreenLegacyFontTiles:
	ld de, FontBattleExtra + 17 tiles ; '◀'
	ld hl, vTiles2 tile '◀'
	lb bc, BANK(FontBattleExtra), 1
	call Get2bppViaHDMA
	ld de, FontBattleExtra + 19 tiles ; '<ID>' and '№'
	ld hl, vTiles2 tile '<ID>'
	lb bc, BANK(FontBattleExtra), 2
	call Get2bppViaHDMA
	ret
