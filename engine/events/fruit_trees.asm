FruitTreeScript::
	callasm GetCurTreeFruit
	opentext
	readmem wCurFruit
	getitemname STRING_BUFFER_3, USE_SCRIPT_VAR
	callasm GetCurTreeFruitPluralName
	writetext FruitBearingTreeText
	promptbutton
	callasm TryResetFruitTrees
	callasm CheckFruitTree
	iffalse .fruit
	writetext NothingHereText
	waitbutton
	sjump .end

.fruit
	writetext HeyItsFruitText
	readmem wCurFruit
	giveitem ITEM_FROM_MEM, 2
	iffalse .packisfull
	promptbutton
	writetext ObtainedTwoFruitText
	callasm PickedFruitTree
	callasm FruitTreeItemPicNotify
	callasm GetCurTreeFruitPocketName
	writetext PutTwoFruitInPocketText
	sjump .end

.packisfull
	promptbutton
	writetext FruitPackIsFullText
	waitbutton

.end
	closetext
	end

GetCurTreeFruit:
	ld a, [wCurFruitTree]
	dec a
	call GetFruitTreeItem
	ld [wCurFruit], a
	ret

GetCurTreeFruitPluralName:
	ld a, [wCurFruit]
	ld c, a
	ld hl, FruitTreePluralNames
.loop
	ld a, [hli]
	cp -1
	jr z, .use_item_name
	cp c
	jr z, .copy
.skip_name
	ld a, [hli]
	cp '@'
	jr nz, .skip_name
	jr .loop

.use_item_name
	ld hl, wStringBuffer3
.copy
	ld de, wStringBuffer4
.copy_loop
	ld a, [hli]
	ld [de], a
	inc de
	cp '@'
	jr nz, .copy_loop
	ret

TryResetFruitTrees:
	ld hl, wDailyFlags1
	bit DAILYFLAGS1_ALL_FRUIT_TREES_F, [hl]
	ret nz
	jp ResetFruitTrees

CheckFruitTree:
	ld b, 2
	call GetFruitTreeFlag
	ld a, c
	ld [wScriptVar], a
	ret

PickedFruitTree:
	farcall StubbedTrainerRankings_FruitPicked
	ld b, 1
	jp GetFruitTreeFlag

FruitTreeItemPicNotify:
	farcall ItemPicNotify
	ret

GetCurTreeFruitPocketName:
	farcall CheckItemPocket
	ld de, FruitTreeBerryPocketName
	ld a, [wItemAttributeValue]
	cp APRICORN
	jr nz, .copy
	ld de, FruitTreeApricornPocketName
.copy
	ld hl, wStringBuffer3
	jp CopyName2

ResetFruitTrees:
	xor a
	ld hl, wFruitTreeFlags
rept (NUM_FRUIT_TREES + 7) / 8 - 1
	ld [hli], a
endr
	ld [hl], a
	ld hl, wDailyFlags1
	set DAILYFLAGS1_ALL_FRUIT_TREES_F, [hl]
	ret

GetFruitTreeFlag:
	push hl
	push de
	ld a, [wCurFruitTree]
	dec a
	ld e, a
	ld d, 0
	ld hl, wFruitTreeFlags
	call FlagAction
	pop de
	pop hl
	ret

GetFruitTreeItem:
	push hl
	push de
	ld e, a
	ld d, 0
	ld hl, FruitTreeItems
	add hl, de
	ld a, [hl]
	pop de
	pop hl
	ret

INCLUDE "data/items/fruit_trees.asm"

FruitTreePluralNames:
	db BERRY,        "Berries@"
	db PSNCUREBERRY, "PsnCureBerries@"
	db BITTER_BERRY, "Bitter Berries@"
	db PRZCUREBERRY, "PrzCureBerries@"
	db MYSTERYBERRY, "MysteryBerries@"
	db ICE_BERRY,    "Ice Berries@"
	db MINT_BERRY,   "Mint Berries@"
	db BURNT_BERRY,  "Burnt Berries@"
	db RED_APRICORN, "Red Apricorns@"
	db BLU_APRICORN, "Blu Apricorns@"
	db BLK_APRICORN, "Blk Apricorns@"
	db WHT_APRICORN, "Wht Apricorns@"
	db PNK_APRICORN, "Pnk Apricorns@"
	db GRN_APRICORN, "Grn Apricorns@"
	db YLW_APRICORN, "Ylw Apricorns@"
	db -1

FruitTreeBerryPocketName:
	db "Berry Pocket@"

FruitTreeApricornPocketName:
	db "Apricorn Box@"

FruitBearingTreeText:
	text_far _FruitBearingTreeText
	text_end

HeyItsFruitText:
	text_far _HeyItsFruitText
	text_end

ObtainedFruitText:
	text_far _ObtainedFruitText
	text_end

ObtainedTwoFruitText:
	text_far _ObtainedTwoFruitText
	text_end

PutTwoFruitInPocketText:
	text_far _PutTwoFruitInPocketText
	text_end

FruitPackIsFullText:
	text_far _FruitPackIsFullText
	text_end

NothingHereText:
	text_far _NothingHereText
	text_end
