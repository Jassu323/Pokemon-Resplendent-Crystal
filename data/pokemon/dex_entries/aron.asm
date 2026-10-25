	db "Iron Armor@"
	dw 104, 1323

.page1::
.line0:
	db "A Pokémon that is"
ASSERT @ - .line0 == 17
.line1:
	next "clad in steel"
ASSERT @ - .line1 == 14
.line2:
	next "armor. A new suit@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "of armor is made"
ASSERT @ - .line3 == 16
.line4:
	next "when it evolves."
ASSERT @ - .line4 == 17
.line5:
	next "The old, discarded@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "armor is salvaged"
ASSERT @ - .line6 == 17
.line7:
	next "as metal for"
ASSERT @ - .line7 == 13
.line8:
	next "making iron@"
ASSERT @ - .line8 == 13

.page4::
.line9:
	db "products.@"
ASSERT @ - .line9 == 10
