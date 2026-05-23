SwitchItemsInBag:
	ld a, [wSwitchItem]
	and a
	jr z, .init
	ld b, a
	ld a, [wScrollingMenuCursorPosition]
	inc a
	cp b
	jr z, .trivial
	ld a, [wScrollingMenuCursorPosition]
	call ItemSwitch_GetNthItem
	ld a, [hl]
	cp -1
	ret z
	ld a, [wSwitchItem]
	dec a
	ld [wSwitchItem], a
	call .try_combining_stacks
	jp c, .combine_stacks
	ld a, [wScrollingMenuCursorPosition]
	ld c, a
	ld a, [wSwitchItem]
	cp c
	jr c, .above
	jr .below

.init:
	ld a, [wScrollingMenuCursorPosition]
	inc a
	ld [wSwitchItem], a
	ret

.trivial:
	xor a
	ld [wSwitchItem], a
	ret

.below:
	ld a, [wSwitchItem]
	call ItemSwitch_CopyItemToBuffer
	ld a, [wScrollingMenuCursorPosition]
	ld d, a
	ld a, [wSwitchItem]
	ld e, a
	call ItemSwitch_GetItemOffset
	push bc
	ld a, [wSwitchItem]
	call ItemSwitch_GetNthItem
	dec hl
	push hl
	call ItemSwitch_GetItemFormatSize
	add hl, bc
	ld d, h
	ld e, l
	pop hl
	pop bc
	call ItemSwitch_BackwardsCopyBytes
	ld a, [wScrollingMenuCursorPosition]
	call ItemSwitch_CopyBufferToItem
	xor a
	ld [wSwitchItem], a
	ret

.above:
	ld a, [wSwitchItem]
	call ItemSwitch_CopyItemToBuffer
	ld a, [wScrollingMenuCursorPosition]
	ld d, a
	ld a, [wSwitchItem]
	ld e, a
	call ItemSwitch_GetItemOffset
	push bc
	ld a, [wSwitchItem]
	call ItemSwitch_GetNthItem
	ld d, h
	ld e, l
	call ItemSwitch_GetItemFormatSize
	add hl, bc
	pop bc
	call CopyBytes
	ld a, [wScrollingMenuCursorPosition]
	call ItemSwitch_CopyBufferToItem
	xor a
	ld [wSwitchItem], a
	ret

.try_combining_stacks:
	ld a, [wSwitchItem]
	call ItemSwitch_GetNthItem
	ld d, h
	ld e, l
	ld a, [wScrollingMenuCursorPosition]
	call ItemSwitch_GetNthItem
	ld a, [de]
	cp [hl]
	jr nz, .no_combine
	ld a, [wScrollingMenuCursorPosition]
	call ItemSwitch_GetItemQuantity
	cp MAX_ITEM_STACK
	jr z, .no_combine
	ld a, [wSwitchItem]
	call ItemSwitch_GetItemQuantity
	cp MAX_ITEM_STACK
	jr nz, .combine
.no_combine
	and a
	ret
.combine
	scf
	ret

.combine_stacks:
	ld a, [wSwitchItem]
	call ItemSwitch_GetNthItem
	inc hl
	push hl
	ld a, [wScrollingMenuCursorPosition]
	call ItemSwitch_GetNthItem
	inc hl
	ld a, [hl]
	pop hl
	add [hl]
	cp MAX_ITEM_STACK + 1
	jr c, .merge_stacks
	sub MAX_ITEM_STACK
	push af
	ld a, [wScrollingMenuCursorPosition]
	call ItemSwitch_GetNthItem
	inc hl
	ld [hl], MAX_ITEM_STACK
	ld a, [wSwitchItem]
	call ItemSwitch_GetNthItem
	inc hl
	pop af
	ld [hl], a
	xor a
	ld [wSwitchItem], a
	ret

.merge_stacks:
	push af
	ld a, [wScrollingMenuCursorPosition]
	call ItemSwitch_GetNthItem
	inc hl
	pop af
	ld [hl], a
	ld hl, wMenuData_ItemsPointerAddr
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, [wSwitchItem]
	cp [hl]
	jr nz, .not_combining_last_item
	dec [hl]
	ld a, [wSwitchItem]
	call ItemSwitch_GetNthItem
	ld [hl], -1 ; end
	xor a
	ld [wSwitchItem], a
	ret

.not_combining_last_item:
	dec [hl]
	call ItemSwitch_GetItemFormatSize
	push bc
	ld a, [wSwitchItem]
	call ItemSwitch_GetNthItem
	pop bc
	push hl
	add hl, bc
	pop de
.copy_loop
	ld a, [hli]
	ld [de], a
	inc de
	cp -1 ; end?
	jr nz, .copy_loop
	xor a
	ld [wSwitchItem], a
	ret

ItemSwitch_CopyItemToBuffer:
	call ItemSwitch_GetNthItem
	ld de, wSwitchItemBuffer
	call ItemSwitch_GetItemFormatSize
	call CopyBytes
	ret

ItemSwitch_CopyBufferToItem:
	call ItemSwitch_GetNthItem
	ld d, h
	ld e, l
	ld hl, wSwitchItemBuffer
	call ItemSwitch_GetItemFormatSize
	call CopyBytes
	ret

ItemSwitch_GetNthItem:
	push af
	call ItemSwitch_GetItemFormatSize
	ld hl, wMenuData_ItemsPointerAddr
	ld a, [hli]
	ld h, [hl]
	ld l, a
	inc hl
	pop af
	call AddNTimes
	ret

ItemSwitch_GetItemOffset:
	push hl
	call ItemSwitch_GetItemFormatSize
	ld a, d
	sub e
	jr nc, .dont_negate
	dec a
	cpl
.dont_negate
	ld hl, 0
	call AddNTimes
	ld b, h
	ld c, l
	pop hl
	ret

ItemSwitch_GetItemFormatSize:
	push hl
	ld a, [wMenuData_ScrollingMenuItemFormat]
	ld c, a
	ld b, 0
	ld hl, .item_format_sizes
	add hl, bc
	add hl, bc
	ld c, [hl]
	inc hl
	ld b, [hl]
	pop hl
	ret

.item_format_sizes:
; entries correspond to SCROLLINGMENU_ITEMS_* constants
	dw 0 ; unused
	dw 1 ; SCROLLINGMENU_ITEMS_NORMAL
	dw 2 ; SCROLLINGMENU_ITEMS_QUANTITY

ItemSwitch_GetItemQuantity:
	push af
	call ItemSwitch_GetItemFormatSize
	ld a, c
	cp 2
	jr nz, .no_quantity
	pop af
	call ItemSwitch_GetNthItem
	inc hl
	ld a, [hl]
	ret

.no_quantity
	pop af
	ld a, 1
	ret

ItemSwitch_BackwardsCopyBytes:
.loop
	ld a, [hld]
	ld [de], a
	dec de
	dec bc
	ld a, b
	or c
	jr nz, .loop
	ret

SortItemsInBag:
	call ItemSort_LoadCurrentPocket
	ret nc
	ld a, [hl]
	cp 2
	jr nc, .sort
	and a
	ret

.sort
	dec a
	ld [wBuffer1], a

.outer_loop
	xor a
	ld [wMenuCursorPosition], a
	ld [wStringBuffer2], a
	ld a, [wBuffer1]
	ld c, a

.inner_loop
	push bc
	ld a, [wMenuCursorPosition]
	call ItemSort_CompareAdjacent
	jr nc, .next_item
	ld a, [wMenuCursorPosition]
	call ItemSort_SwapAdjacent
	ld a, 1
	ld [wStringBuffer2], a

.next_item
	ld hl, wMenuCursorPosition
	inc [hl]
	pop bc
	dec c
	jr nz, .inner_loop
	ld a, [wStringBuffer2]
	and a
	jr z, .done
	ld hl, wBuffer1
	dec [hl]
	jr nz, .outer_loop
.done
	scf
	ret

ItemSort_CompareAdjacent:
	push af
	call ItemSwitch_GetNthItem
	ld a, [hl]
	call ItemSort_GetSortRank
	ld b, a
	pop af
	push bc
	inc a
	call ItemSwitch_GetNthItem
	ld a, [hl]
	call ItemSort_GetSortRank
	pop bc
	cp b
	ret

ItemSort_GetSortRank:
	and a
	jr z, .unknown
	cp NUM_ITEMS + 1
	jr nc, .unknown
	dec a
	ld e, a
	ld d, 0
	ld hl, ItemSortRankTable
	add hl, de
	ld a, [hl]
	ret

.unknown
	ld a, $ff
	ret

ItemSort_SwapAdjacent:
	push af
	call ItemSwitch_GetNthItem
	ld d, h
	ld e, l
	pop af
	inc a
	call ItemSwitch_GetNthItem
	call ItemSwitch_GetItemFormatSize
	jp SwapBytes

ItemSort_LoadCurrentPocket:
	ld a, [wCurPocket]
	cp NUM_POCKETS
	ret nc
	ld e, a
	ld d, 0
	ld hl, .pocket_data
	add hl, de
	add hl, de
	add hl, de
	ld a, [hli]
	ld [wMenuData_ItemsPointerAddr], a
	ld e, a
	ld a, [hli]
	ld [wMenuData_ItemsPointerAddr + 1], a
	ld d, a
	ld a, [hl]
	ld [wMenuData_ScrollingMenuItemFormat], a
	ld h, d
	ld l, e
	scf
	ret

.pocket_data
	dwb wNumItems, SCROLLINGMENU_ITEMS_QUANTITY
	dwb wNumBalls, SCROLLINGMENU_ITEMS_QUANTITY
	dwb wNumKeyItems, SCROLLINGMENU_ITEMS_NORMAL
	dwb wNumBerries, SCROLLINGMENU_ITEMS_QUANTITY
	dwb wNumMedicine, SCROLLINGMENU_ITEMS_QUANTITY

ItemSortRankTable:
; Entries correspond to item IDs $01-NUM_ITEMS. Ranks are generated from
; ItemNames with "#" treated as "POKE" for display-alphabetical sorting.
	table_width 1
	; $01-$10
	db  81, 184,  19,  53, 112, 152,   8,  95,   2,  20,  63,   3, 106,  48,  84,  61
	; $11-$20
	db 148, 116,  37, 127,  82,  42, 181, 186, 153,  60, 118,  64,  23,  77,  22, 124
	; $21-$30
	db 188,  67,  88, 103, 113,  47, 129,  86,  56, 149,  85,  29, 154,  45, 140,  69
	; $31-$40
	db 189, 155, 190, 192, 191,  28,  65, 156,  40, 104,  51, 135, 150, 117,  38,  83
	; $41-$50
	db  33, 126, 133, 130,  98,  27, 136,  93, 121, 120,  50, 141, 134, 119,  21,  62
	; $51-$60
	db 111,  66,  11,  89, 125, 182,   9, 137,  15, 157,   1, 193,  54,  26, 100, 183
	; $61-$70
	db 187,  12,  14, 158, 110,  13, 138, 109, 146, 139, 101,  80,  91, 108,  10,  39
	; $71-$80
	db 142, 122,  55,  16,  90, 180,  44, 159,  35,  34,  58, 128,  57,  76,  24,  79
	; $81-$90
	db  32,  73, 145, 144,   4, 107, 160, 161, 162,  25,   6, 132, 163, 164,  87,  30
	; $91-$a0
	db 165,  68, 166, 167, 168,  99,  31,   7, 169, 170, 171, 131,  59,  43,  70,  78
	; $a1-$b0
	db  41, 172,  71,  46,  94,  74, 102,  52, 147, 114, 173, 185,   5,  49, 143, 174
	; $b1-$c0
	db 105, 123, 175,  18, 151,  72, 115,  75,  36,  96,  17,  97,  92, 176, 177, 178
	; $c1-$c1
	db 179
	assert_table_length NUM_ITEMS
