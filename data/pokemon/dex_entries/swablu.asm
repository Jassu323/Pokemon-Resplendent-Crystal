	db "Cotton Bird@"
	dw 104, 26

.page1::
.line0:
	db "A Pokémon that has"
ASSERT @ - .line0 == 18
.line1:
	next "wings like cottony"
ASSERT @ - .line1 == 19
.line2:
	next "clouds. After@"
ASSERT @ - .line2 == 15

.page2::
.line3:
	db "enduring winter,"
ASSERT @ - .line3 == 16
.line4:
	next "in which little"
ASSERT @ - .line4 == 16
.line5:
	next "food is available,@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "Swablu flocks move"
ASSERT @ - .line6 == 18
.line7:
	next "closer to towns in"
ASSERT @ - .line7 == 19
.line8:
	next "the spring.@"
ASSERT @ - .line8 == 13
